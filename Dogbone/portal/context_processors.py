import os
import json
import logging
from django.conf import settings
from api_v1.user.endpoints import user_to_dict, CurrentUserActiveSubscriptionDetailView
from .tools import random_str


class GitHeadRevisionTag(object):
    """ thanks to https://djangosnippets.org/snippets/1808/ """

    head = None

    @staticmethod
    def _get_head():
        """ Get the hash of the git HEAD """
        git_dir = os.path.normpath(os.path.join(settings.PROJECT_ROOT, '.git'))

        # Read the HEAD ref
        try:
            fhead = open(os.path.join(git_dir, 'HEAD'), 'r')
            ref_name = fhead.readline().split(" ")[1].strip()
            fhead.close()

            # Read the commit id
            fref = open(os.path.join(git_dir, ref_name), 'r')
            ref = fref.readline().strip()
            fref.close()
        except IOError:
            ref = random_str(20)

        return unicode(ref)

    @staticmethod
    def get_head():
        """ Returns the cached hash of the git HEAD """
        if GitHeadRevisionTag.head is None:
            GitHeadRevisionTag.head = GitHeadRevisionTag._get_head()
        return GitHeadRevisionTag.head


def git_revision(request):
    return {
        'git_revision': GitHeadRevisionTag.get_head()
    }


def global_settings(request):
    try:
        react_local_address = settings.REACT_LOCAL_ADDRESS
    except AttributeError:
        react_local_address = 'http://0.0.0.0:3000'
    return {
        'NODEJS_SERVER': settings.NODEJS_SERVER,
        'INTERCOM_ENV': settings.INTERCOM_ENV,
        'HOT_LOAD': getattr(settings, 'HOT_LOAD', False),
        'REACT_LOCAL_ADDRESS': react_local_address
    }


def server_side_data(request):
    user_json_data = {}
    subscription_json_data = {}
    try:
        if request.user and not request.user.is_anonymous():
            user_json_data = user_to_dict(request.user)
            subscription_json_data = CurrentUserActiveSubscriptionDetailView.to_dict(request.user)
    except Exception as e:
        logging.error('Strange thing happened: %s', str(e))

    return {
        'user_json_dict': json.dumps(user_json_data),
        'subscription_json_dict': json.dumps(subscription_json_data)
    }
