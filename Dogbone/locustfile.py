import os
import sys
from locust import HttpLocust, TaskSet
from django.core.urlresolvers import reverse
import requests
from portal.tools import random_str

requests.packages.urllib3.disable_warnings()

sys.path.append(os.path.join(os.path.dirname(__file__)))
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dogbone.settings")


test_username = 'beagle_test_locust'
test_password = 'l0cust666'
test_email = 'locust@sniffthefineprint.com'


def login_process(l):
    # go to main page
    l.client.get(reverse('index'), verify=False)

    # get the register page
    l.client.get(reverse('register'), verify=False)

    # get the reset pass page
    l.client.get(reverse('reset_password'), verify=False)

    # try to login
    r = l.client.get(reverse('login'), verify=False)
    
    csrf = l.client.cookies['csrftoken']
    r = l.client.post(reverse('login'), {"csrfmiddlewaretoken": csrf,
                                     "email": test_email,
                                     "password": test_password + random_str(1)}, verify=False)


    csrf = l.client.cookies['csrftoken']
    r = l.client.post(reverse('login'), {"csrfmiddlewaretoken": csrf,
                                     "email": test_email + random_str(1),
                                     "password": test_password}, verify=False)

    csrf = l.client.cookies['csrftoken']
    r = l.client.post(reverse('login'), {"csrfmiddlewaretoken": csrf,
                                     "email": test_email,
                                     "password": test_password}, verify=False)


def index(l):
    l.client.get(reverse('index'), verify=False)


def login(l):
    l.client.get(reverse('login'), verify=False)


def reset_password(l):
    l.client.get(reverse('reset_password'), verify=False)


def dashboard(l):
    l.client.get(reverse('dashboard'), verify=False)


def account(l):
    l.client.get(reverse('account'), verify=False)


def document_aggregated_list(l):
    l.client.get(reverse('document_aggregated_list_view'), verify=False)


def document_list(l):
    r = l.client.get(reverse('document_list_view'), verify=False)

    # print '=' * 30
    # print r.content
    # print '=' * 30


def me_detail(l):
    l.client.get(reverse('me_detail_view'), verify=False)


def me_profile_detail(l):
    l.client.get(reverse('me_profile_detail_view'), verify=False)


def me_received_invitations_list(l):
    l.client.get(reverse('me_received_invitations_list_view'), verify=False)


def me_issued_invitations_list(l):
    l.client.get(reverse('me_issued_invitations_list_view'), verify=False)


def me_collaborators_list(l):
    l.client.get(reverse('me_collaborators_list_view'), verify=True)


def inbox_list(l):
    l.client.get(reverse('inbox_list_view'), verify=True)


class UserBehavior(TaskSet):
    tasks = {index: 2,
             login: 1,
             reset_password: 1,
             dashboard: 5,
             account: 5,
             document_aggregated_list: 3,
             document_list: 3,
             me_detail: 5,
             me_profile_detail: 1,
             me_received_invitations_list: 3,
             me_issued_invitations_list: 1,
             me_collaborators_list: 2,
             inbox_list: 5}

    def on_start(self):
        login_process(self)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000