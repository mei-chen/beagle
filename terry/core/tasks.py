# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import logging
import os
import re
import requests
import shutil

from urllib import urlencode
from urllib2 import urlopen

# Django
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now

# App
from realtime.notify import NotificationManager

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger

# Snoopy
from terry.utils import (
    CaptureStdout, clone_repo, parse_snoopy_output, check_if_repo_exists,
    clean_repo_url,  GITHUB_OAUTH_URL, BITBUCKET_OAUTH_URL, GITLAB_OAUTH_URL,
    InvalidUrl
)
from reports.models import Report, ReportShared
from reports.utils import LICENSES_RISKS
from snoopy import snoo
from marketing.subscriptions import SUBSCRIPTION_ALLOWANCES, FREE
from marketing.models import PurchasedSubscription

logger = get_task_logger(__name__)


FAKE_USERNAME = 'username'
FAKE_PASSWORD = 'password'
access_token_re = re.compile(r'access_token=([^&]+)')

SLACK_NOTIF = 'Unrecognized license encountered: %s (%s)'


class AllowedPrivateReposCountExceeded(Exception):
    pass


@shared_task
def analyze_git_repo(session_key, git_url, user_pk, task_uuid,
                     report_uuid=None, github_app_data=None):
    repo_meta = None

    try:
        user = User.objects.get(pk=user_pk)

        credentials = {}
        if user.profile.github_access_token:
            credentials['github'] = {
                'access_token': user.profile.github_access_token
            }
        else:
            # Hack for raising exception immediately instead of prompting for
            # credentials, when trying to fetch private repos.
            # Does not change behavior for public repos, since for cloning them
            # credentials are not needed at all, so even invalid ones are OK.
            credentials['github'] = {'username': FAKE_USERNAME,
                                     'password': FAKE_PASSWORD}

        if user.profile.bitbucket_refresh_token:
            credentials['bitbucket'] = {
                'access_token': user.profile.bitbucket_access_token
            }
        else:
            credentials['bitbucket'] = {}

        if user.profile.gitlab_refresh_token:
            credentials['gitlab'] = {
                'access_token': user.profile.gitlab_access_token
            }
        else:
            credentials['gitlab'] = {'username': FAKE_USERNAME,
                                     'password': FAKE_PASSWORD}

        if not git_url.startswith('http'):
            git_url = 'https://' + git_url

        git_url, repo_meta = clean_repo_url(git_url)

        try:
            public_repo = check_if_repo_exists(git_url)
        except InvalidUrl:
            public_repo = False
            raise

        unallowed_repo_reprocess = False
        if report_uuid:
            report = Report.objects.get(uuid=report_uuid)
            if ('exception' in report.content and
                report.content['exception'].startswith(
                    'AllowedPrivateReposCountExceeded')):
                unallowed_repo_reprocess = True

        # If github_app_data is provided than its a task from GitHub App, we do not limit these
        if not (public_repo or github_app_data or
                    (report_uuid and not unallowed_repo_reprocess)):
            subscription = PurchasedSubscription.get_user_subscription(user)
            if subscription:
                allowed_repos = SUBSCRIPTION_ALLOWANCES[subscription.subscription]
            else:
                allowed_repos = SUBSCRIPTION_ALLOWANCES[FREE]

            if allowed_repos != -1:
                user_private_repos = Report.objects.filter(
                    user=user, public_repo=False, successful=True).count()

                if user_private_repos >= allowed_repos:
                    raise AllowedPrivateReposCountExceeded(allowed_repos)

        cloned_path, tmp_dir = clone_repo(git_url, credentials)

        try:
            with CaptureStdout(session_key, task_uuid) as lines:
                output = snoo.main(cloned_path)
            content = parse_snoopy_output(output)
            content['exception'] = ''
        finally:
            shutil.rmtree(tmp_dir)
            # Print results to console only after full repo analysis
            # (use warning level for better visualization)
            logger.warning(os.linesep.join(lines))

    except Exception as e:
        content = {'exception': '%s: %s' % (e.__class__.__name__, str(e))}
        raise

    finally:
        content['git_url'] = git_url
        if repo_meta:
            content['repo_name'] = repo_meta['repo_name']
            content['branch'] = repo_meta['branch']

        # Check content status
        successful = False
        if content['exception']:
            content['status'] = 'red'
        elif content['error']:
            content['status'] = 'yellow'
        else:
            content['status'] = 'green'
            successful = True

        # save report to db
        if report_uuid:
            report = Report.objects.get(uuid=report_uuid)
            report.created_at = now()
            report.content = content
            report.public_repo = public_repo
            report.successful = successful
        else:
            report = Report(
                url=git_url,
                content=content,
                user=user,
                public_repo=public_repo,
                successful=successful
            )

        report.save()

        # Slack the unrecognized licenses
        if 'licenses' in content and settings.SLACK_WEBHOOK:
            all_treat_as = set()
            for license in content['licenses']:
                all_treat_as.update(license[7])
            for treat_as in all_treat_as:
                if (treat_as not in LICENSES_RISKS and
                    treat_as not in ['- NO LICENSE SPECIFIED -', '- FETCH ERROR -']):
                        send_slack_notification.delay(SLACK_NOTIF % (treat_as, git_url))

        data = {
            'uuid': str(report.uuid),
            'type': 'license_report',
            'task_uuid': task_uuid
        }

        message = NotificationManager.notify_client(session_key)
        message.set_message(data)
        logger.info(message.send())

        # Notify GitHub App
        if github_app_data:
            r_shared = ReportShared.objects.create(report=report, user=user)
            report_link = github_app_data['url'] + r_shared.share_url()

            if content['status'] == 'green':
                state = 'success'
                description = 'Your dependency stack is {}% open'.format(
                    100 - report.content_for_frontend['overall_risk'])

            elif content['status'] == 'yellow':
                state = 'failure'
                description = content['error']

            else:
                state = 'error'
                description = content['exception']

            # We can also provide target_url as link for the report
            github_app_send_commit_status.delay(
                statuses_url=github_app_data['statuses_url'],
                access_token=user.profile.github_access_token,
                state=state,
                description=description,
                target_url=report_link
            )

            logger.info('Github App notification sent: %s, %s for %s' % (
                state, description, github_app_data['statuses_url']))


@shared_task
def get_access_token_github(session_key, user_pk, code):
    response = urlopen(GITHUB_OAUTH_URL % (settings.GITHUB_OAUTH_CLIENT_ID,
                                           settings.GITHUB_OAUTH_SECRET,
                                           code))
    payload = response.read()

    access_token = access_token_re.search(payload).group(1)

    user = User.objects.get(pk=user_pk)
    user.profile.github_access_token = access_token
    user.save()

    data = {'type': 'msg', 'text': 'GitHub access token successfully received'}
    message = NotificationManager.notify_client(session_key)
    message.set_message(data)
    logger.info(message.send())


@shared_task
def get_access_token_github_app(code):
    response = urlopen(GITHUB_OAUTH_URL % (settings.GITHUB_APP_ID,
                                           settings.GITHUB_APP_SECRET,
                                           code))
    payload = response.read()

    return access_token_re.search(payload).group(1)


@shared_task
def get_refresh_token_bitbucket(session_key, user_pk, code):
    response = requests.post(
        BITBUCKET_OAUTH_URL,
        data={'grant_type': 'authorization_code', 'code': code},
        auth=requests.auth.HTTPBasicAuth(
            settings.BITBUCKET_OAUTH_CLIENT_ID,
            settings.BITBUCKET_OAUTH_SECRET
        )
    )
    payload = response.json()

    refresh_token = payload['refresh_token']

    user = User.objects.get(pk=user_pk)
    user.profile.bitbucket_refresh_token = refresh_token
    user.save()

    data = {'type': 'msg', 'text': 'Bitbucket refresh token successfully received'}
    message = NotificationManager.notify_client(session_key)
    message.set_message(data)
    logger.info(message.send())


@shared_task
def get_refresh_token_gitlab(session_key, user_pk, code, callback_url):
    response = requests.post(
        GITLAB_OAUTH_URL + '?' + urlencode({
            'grant_type': 'authorization_code',
            'client_id': settings.GITLAB_OAUTH_CLIENT_ID,
            'client_secret': settings.GITLAB_OAUTH_SECRET,
            'code': code,
            'redirect_uri': callback_url
        })
    )
    payload = response.json()

    refresh_token = payload['refresh_token']

    user = User.objects.get(pk=user_pk)
    user.profile.gitlab_refresh_token = refresh_token
    user.save()

    data = {'type': 'msg', 'text': 'GitLab refresh token successfully received'}
    message = NotificationManager.notify_client(session_key)
    message.set_message(data)
    logger.info(message.send())


@shared_task
def send_slack_notification(message,
                            channel=settings.SLACK_CHANNEL,
                            username='Terry Bot',
                            icon_emoji=':robot_face:'):
    """
    Send a slackbot message
    :param message: The actual message
    :param channel: The channel: #dev, #general, @admin etc
    :param username: Bot name
    :param channel: You can attach emoji like: :monkey_face:, :v: etc
    """

    data = {
        'text': message,
        'channel': channel,
        'username': username,
        'icon_emoji': icon_emoji
    }
    try:
        logging.info('Slack sending message: "%s" to channel: "%s"' % (message, channel))
        response = requests.post(settings.SLACK_WEBHOOK, json=data)
        logging.info('Slack message response %s: %s' % (response.status_code, response.text))
        return True
    except:
        return False


@shared_task
def github_app_send_commit_status(statuses_url,
                                  access_token,
                                  state='pending',
                                  description="check is in progress...",
                                  target_url=None):
    data = {
        'state': state,
        'context': 'Terry Licenses check',
        'description': description
    }

    if target_url:
        data['target_url'] = target_url

    response = requests.post(
        statuses_url,
        headers={'Authorization': 'token %s' % access_token},
        data=json.dumps(data)
    )
