import json
import os
import re
import shutil
import six
import sys
import tempfile
from StringIO import StringIO
from urllib2 import urlopen, HTTPError, Request

import hglib
import requests
from git import Git, GitCommandError

from realtime.notify import NotificationManager
from snoopy.snoo import STATUS_CODES

repo_name_re = re.compile(r'(^https?://.+?/([^/]+)/([^/]+))(?:/(tree|blob|branch|src)/(.+))?/?')


BITBUCKET_API = 'https://api.bitbucket.org/2.0/repositories/{0}/{1}'
GITHUB_API = 'https://api.github.com/repos/{0}/{1}'
GITLAB_API = 'https://gitlab.com/api/v4/projects/{0}%2F{1}'

GITHUB_OAUTH_URL = 'https://github.com/login/oauth/access_token?client_id=%s&client_secret=%s&code=%s'
BITBUCKET_OAUTH_URL = 'https://bitbucket.org/site/oauth2/access_token'
GITLAB_OAUTH_URL = 'https://gitlab.com/oauth/token'

GITHUB_USER_REPOS = 'https://api.github.com/user/repos'
BITBUCKET_USER_REPOS = 'https://api.bitbucket.org/2.0/repositories?role=member'
GITLAB_USER_REPOS = 'https://gitlab.com/api/v4/projects?membership=true&simple=true'


class InvalidUrl(Exception):
    pass


class RepositoryNotFound(Exception):
    pass


class UnsupportedSourceCodeManagerType(Exception):
    pass


class NoSourceCodeManagerTypeFound(Exception):
    pass


class UnsupportedRepository(Exception):
    pass


class StringIOCustom(StringIO, object):

    def __init__(self, session_key, task_uuid, *args, **kwargs):
        super(StringIOCustom, self).__init__(self, *args, **kwargs)
        self.session_key = session_key
        self.task_uuid = task_uuid

        self.p_m_flags = {
            'pip': {'manifest_found': False},
            'npm': {'manifest_found': False},
            'bower': {'manifest_found': False},
            'ruby_gem': {'manifest_found': False},
            'maven': {'manifest_found': False},
            'composer': {'manifest_found': False},
        }

    def write(self, s):
        super(StringIOCustom, self).write(s)

        for p_m in ['pip', 'npm', 'bower', 'ruby_gem', 'maven', 'composer']:
            if '> %s >>' % p_m in s:
                self.p_m_flags[p_m]['manifest_found'] = True

            elif ('(%s)' % p_m in s and self.p_m_flags[p_m]['manifest_found']):
                data = {
                    'type': 'progress',
                    'text': 'Parsing started',
                    'package_manager': p_m,
                    'task_uuid': self.task_uuid
                }
                message = NotificationManager.notify_client(self.session_key)
                message.set_message(data)
                message.send()


class CaptureStdout(list):
    """
    Context manager for capturing stdout.
    Usage:

        with CaptureStdout() as output:
            do_something(my_object)

    Output will be a list containing the lines printed by the function call.
    """

    def __init__(self, session_key, task_uuid, *args, **kwargs):
        super(CaptureStdout, self).__init__(*args, **kwargs)
        self.session_key = session_key
        self.task_uuid = task_uuid

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIOCustom(self.session_key,
                                                     self.task_uuid)
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def clone_repo(git_url, credentials):
    _, repo_data = clean_repo_url(git_url)
    git_url = repo_data['clean_url']
    user_name = repo_data['user_name']
    repo_name = repo_data['repo_name']
    branch = repo_data['branch']

    repos_dir = tempfile.mkdtemp()
    cloned_path = os.path.join(repos_dir, repo_name)

    if 'bitbucket.org' in git_url:
        bitbucket_api_url = BITBUCKET_API.format(user_name, repo_name)
        credentials = credentials['bitbucket']
        req = Request(bitbucket_api_url)
        if 'access_token' in credentials:
            req.add_header(
                'Authorization', 'Bearer %s' % credentials['access_token']
            )

        try:
            response_json = json.load(urlopen(req))
        except HTTPError:
            # Don't show any credentials in error messages
            raise RepositoryNotFound(bitbucket_api_url)

        authenticated_url = git_url

        if 'access_token' in credentials:
            authenticated_url = git_url.replace(
                'bitbucket.org',
                'x-token-auth:%s@bitbucket.org' % credentials['access_token']
            )

        scm = response_json['scm']

        if scm == 'git':
            try:
                if branch:
                    Git(working_dir=repos_dir).clone(authenticated_url,
                                                     branch=branch)
                else:
                    Git(working_dir=repos_dir).clone(authenticated_url)
            except GitCommandError:
                # Don't show any credentials in error messages
                raise RepositoryNotFound(git_url)

        elif scm == 'hg':
            repos_dir_mercurial = os.path.join(repos_dir, repo_name)
            if branch:
                hglib.clone(authenticated_url, repos_dir_mercurial,
                            branch=branch)
            else:
                hglib.clone(authenticated_url, repos_dir_mercurial)

        elif scm:
            raise UnsupportedSourceCodeManagerType(scm)

        else:
            raise NoSourceCodeManagerTypeFound(git_url)

    elif 'github.com' in git_url:
        authenticated_git_url = git_url
        credentials = credentials['github']

        if 'access_token' in credentials:
            authenticated_git_url = git_url.replace(
                'github.com', '%s@github.com' % credentials['access_token']
            )
        elif 'username' in credentials and 'password' in credentials:
            authenticated_git_url = git_url.replace(
                'github.com', '%s:%s@github.com' % (credentials['username'],
                                                    credentials['password'])
            )

        try:
            if branch:
                Git(working_dir=repos_dir).clone(authenticated_git_url,
                                                 branch=branch)
            else:
                Git(working_dir=repos_dir).clone(authenticated_git_url)
        except GitCommandError:
            # Don't show any credentials in error messages
            raise RepositoryNotFound(git_url)

    elif 'gitlab.com' in git_url:
        authenticated_git_url = git_url
        credentials = credentials['gitlab']

        if 'access_token' in credentials:
            authenticated_git_url = git_url.replace(
                'gitlab.com', 'oauth2:%s@gitlab.com' % credentials['access_token']
            )
        elif 'username' in credentials and 'password' in credentials:
            authenticated_git_url = git_url.replace(
                'gitlab.com', '%s:%s@gitlab.com' % (credentials['username'],
                                                    credentials['password'])
            )

        try:
            if branch:
                Git(working_dir=repos_dir).clone(authenticated_git_url,
                                                 branch=branch)
            else:
                Git(working_dir=repos_dir).clone(authenticated_git_url)
        except GitCommandError:
            # Don't show any credentials in error messages
            raise RepositoryNotFound(git_url)

    else:
        raise UnsupportedRepository(
            'Only GitHub, Bitbucket and Gitlab repos are supported for now.'
        )

    return cloned_path, repos_dir


def parse_snoopy_output(output):
    status_code, payload = output

    data = {'error': ''}

    if status_code == STATUS_CODES['SUCCESS']:
        stats, data['stats_by_pm'], licenses, links, manifests = payload

        data['stats_header'] = ('License', '#', 'Copyleft')

        data['stats'] = [(lic, cnt, cplft) for lic, cnt, cplft in stats]

        data['licenses_header'] = (
            'Module', 'Library', 'Link', 'Version', 'License', 'Copyleft'
        )

        data['licenses'] = [
            [
                module,
                library,
                link,
                version,
                licences,
                cplft,
                orig_lics,
                treat_as_names
            ]
            for (module, library, version, licences, cplft, orig_lics, treat_as_names), link
            in six.moves.zip(licenses, links)
        ]

        data['manifests'] = manifests

    else:
        data['error'] = 'Unknown error'
        for key, value in STATUS_CODES.items():
            if value == status_code:
                data['error'] = key.replace('_', ' ').capitalize()
                break

    return data


def check_if_repo_exists(url):
    _, repo_data = clean_repo_url(url)
    user_name = repo_data['user_name']
    repo_name = repo_data['repo_name']

    if 'bitbucket.org' in url:
        api_url = BITBUCKET_API.format(user_name, repo_name)
    elif 'github.com' in url:
        api_url = GITHUB_API.format(user_name, repo_name)
    elif 'gitlab.com' in url:
        api_url = GITLAB_API.format(user_name, repo_name)

    try:
        urlopen(api_url)
        exists = True
    except HTTPError:
        exists = False

    return exists


def get_user_repos_github(access_token):
    response = requests.get(
        GITHUB_USER_REPOS,
        headers={'Authorization': 'token %s' % access_token}
    )

    content = response.json()
    repos = [project['html_url'] for project in content]

    return repos


def get_user_repos_bitbucket(access_token):
    response = requests.get(
        BITBUCKET_USER_REPOS,
        headers={'Authorization': 'Bearer %s' % access_token}
    )

    content = response.json()
    repos = [project['links']['html']['href'] for project in content['values']]

    return repos


def get_user_repos_gitlab(access_token):
    response = requests.get(
        GITLAB_USER_REPOS,
        headers={'Authorization': 'Bearer %s' % access_token}
    )

    content = response.json()
    repos = [project['web_url'] for project in content]

    return repos


def clean_repo_url(url):

    if ('bitbucket.org' not in url
            and 'github.com' not in url
            and 'gitlab.com' not in url):
        raise InvalidUrl(url)

    if url.endswith('/'):
        clean_url = url[:-1]
    elif url.endswith('.git'):
        clean_url = url[:-4]
    else:
        clean_url = url

    match = repo_name_re.match(clean_url)
    if not match:
        raise InvalidUrl(url)

    clean_url = match.group(1)
    user_name = match.group(2)
    repo_name = match.group(3)
    separator = match.group(4)
    remainder = match.group(5)

    if remainder and '/' not in remainder and separator in ['tree', 'branch']:
        branch = remainder
        result_url = url
    else:
        branch = None
        result_url = clean_url

    meta = {
        'clean_url': clean_url,
        'user_name': user_name,
        'repo_name': repo_name,
        'branch': branch
    }

    return result_url, meta
