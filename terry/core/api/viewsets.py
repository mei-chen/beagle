import json
import logging

# Django
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.conf import settings

# App
from core.tasks import (
    analyze_git_repo, get_access_token_github, get_access_token_github_app,
    get_refresh_token_bitbucket, get_refresh_token_gitlab,
    github_app_send_commit_status
)

# rest_framework
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class LicensesViewSet(viewsets.ModelViewSet):

    @list_route(methods=['post'])
    def analyze_project(self, request):
        git_url = request.data['git_url'].strip()
        task_uuid = request.data['task_uuid']
        report_uuid = request.data.get('uuid')
        logger.info('[%s] Analyze request received for url: %s',
                    task_uuid, git_url)
        analyze_git_repo.delay(request.session.session_key, git_url,
                               request.user.pk, task_uuid, report_uuid)
        return Response()


class OAuthCallbackViewSet(viewsets.ModelViewSet):

    @list_route(methods=['get'])
    def github(self, request):
        code = request.query_params.get('code')
        logger.info('GitHub account code received: %s' % code)
        if code:
            get_access_token_github(request.session.session_key,
                                    request.user.pk, code)

        redirect_url = '/settings'
        return HttpResponseRedirect(redirect_url)

    @list_route(methods=['get'])
    def bitbucket(self, request):
        code = request.query_params.get('code')
        logger.info('Bitbucket account code received: %s' % code)
        if code:
            get_refresh_token_bitbucket(request.session.session_key,
                                        request.user.pk, code)

        redirect_url = '/settings'
        return HttpResponseRedirect(redirect_url)

    @list_route(methods=['get'])
    def gitlab(self, request):
        code = request.query_params.get('code')
        logger.info('GitLab account code received: %s' % code)
        if code:
            # Discard query parameters
            callback_url = request.build_absolute_uri().split('?')[0]
            get_refresh_token_gitlab(request.session.session_key,
                                     request.user.pk, code, callback_url)

        redirect_url = '/settings'
        return HttpResponseRedirect(redirect_url)


class GithubAppViewset(viewsets.ModelViewSet):

    @list_route(methods=['post'])
    def webhook(self, request):
        data = json.load(request)
        installation_id = data['installation']['id']
        login = data['sender']['login']
        action = data['action']
        logger.info('Github App Webhook called. '
                    'Installation ID: %s. Login: %s. Action: %s' %
                    (installation_id, login, action))

        username = 'GitHubApp-%s' % installation_id
        user, _ = User.objects.get_or_create(username=username)

        if action == 'created':
            user.profile.github_installation_id = installation_id
            user.save()

        elif action == 'deleted':
            user.is_active = False
            user.save()

        elif action in ['synchronize', 'opened']:
            statuses_url = data['pull_request']['statuses_url']
            access_token = user.profile.github_access_token

            # Notify App that analyze has started
            github_app_send_commit_status(statuses_url, access_token)

            repo_url = data['pull_request']['head']['repo']['html_url']
            branch = data['pull_request']['head']['ref']
            git_url = '%s/tree/%s' % (repo_url, branch)

            github_app_data = {
                'statuses_url': statuses_url,
                'url': request.build_absolute_uri('/')[:-1]
            }

            analyze_git_repo.delay(request.session.session_key, git_url,
                                   user.pk, None, github_app_data=github_app_data)

        elif action in ['added', 'closed', 'reopened']:
            # We do not care about these actions
            pass

        else:
            logger.info('Unrecognized action: %s' % action)

        return Response()

    @list_route(methods=['get'])
    def setup(self, request):
        installation_id = request.query_params.get('installation_id')
        request.session['installation_id'] = installation_id

        return HttpResponseRedirect(
            'http://github.com/login/oauth/authorize?client_id=%s' % settings.GITHUB_APP_ID
        )

    @list_route(methods=['get'])
    def register_app(self, request):
        installation_id = request.session['installation_id']
        code = request.query_params.get('code')
        if code:
            access_token = get_access_token_github_app(code)
            user = User.objects.get(profile__github_installation_id=installation_id)
            user.profile.github_access_token = access_token
            user.save()

            logger.info('GitHubApp access token successfully saved '
                        'for Github App user: %s' % user.username)

        return HttpResponseRedirect('https://github.com/settings/apps/authorizations')
