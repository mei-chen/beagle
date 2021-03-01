import csv
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView

# App
from forms import RewriteNameForm, TreatAsNameForm
from reports.models import ReportShared, LicenseStatistic, Report
from snoopy.utils import (
    simplify_lic_name, rewrite_rules_path, treat_as_rules_path,
    treat_as_rules
)
from terry.utils import (
    get_user_repos_github, get_user_repos_bitbucket, get_user_repos_gitlab
)
from marketing.models import PurchasedSubscription
from marketing.subscriptions import ALL_SUBSCRIPTIONS, PAID, ENTERPRISE

RULE_ALREADY_EXISTS_MSG = 'Tried to add rule "{0}: {1}".\nBut rule "{0}: {2}" already exists'
REWRITE_RULE_SUCCESS = 'New rewrite rule added "{0}: {1}"'
TREAT_AS_RULE_SUCCESS = 'New treat as rule added "{0}: {1}"'


def index(request):
    context = {
        'HOT_LOAD': settings.HOT_LOAD,
        'GITHUB_OAUTH_CLIENT_ID': settings.GITHUB_OAUTH_CLIENT_ID,
        'BITBUCKET_OAUTH_CLIENT_ID': settings.BITBUCKET_OAUTH_CLIENT_ID,
        'GITLAB_OAUTH_CLIENT_ID': settings.GITLAB_OAUTH_CLIENT_ID
    }

    # Check if repo analysis was requested from landing page before login
    if request.session.get('git_url'):
        context['GIT_URL'] = request.session['git_url']
        del request.session['git_url']

    # Redirect user to page from which he was logged in
    if request.session.get('redirect_uri'):
        redirect_uri = request.session['redirect_uri']
        del request.session['redirect_uri']
        return redirect(redirect_uri)

    if request.user.is_authenticated():
        template = 'portal/index.html'
    else:
        template = 'portal/landing.html'

    return render(request, template, context)


def interface_public(request, uuid=None):
    report_shared = ReportShared.objects.filter(token=uuid).first()
    if not report_shared:
        raise Http404

    context = {
        'HOT_LOAD': settings.HOT_LOAD,
        'report_uuid': report_shared.report.uuid,
        'report_shared_token': report_shared.token
    }
    return render(request, 'portal/interface_view.html', context)


@login_required(login_url='/accounts/login/')
def interface_private(request, uuid=None):
    context = {}
    return render(request, 'portal/interface_view.html', context)


class UserDetails(APIView):

    def get(self, request):
        user = request.user
        response = {}

        if user.is_authenticated():
            github_token = user.profile.github_access_token
            bitbucket_token = user.profile.bitbucket_access_token
            gitlab_token = user.profile.gitlab_access_token

            reports_public = Report.objects.filter(
                user=user, public_repo=True, successful=True
            ).count()
            reports_private = Report.objects.filter(
                user=user, public_repo=False, successful=True
            ).count()

            subscription = PurchasedSubscription.get_user_subscription(user)

            if subscription:
                if subscription.subscription in ALL_SUBSCRIPTIONS[PAID]:
                    s_name = PAID
                elif subscription.subscription in ALL_SUBSCRIPTIONS[ENTERPRISE]:
                    s_name = ENTERPRISE
                s_expires = subscription.expiration_date
            else:
                s_name = 'FREE'
                s_expires = None

            response = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'github_access_token': bool(github_token),
                'bitbucket_access_token': bool(bitbucket_token),
                'gitlab_access_token': bool(gitlab_token),
                'public_reports_count': reports_public,
                'private_reports_count': reports_private,
                'subscription': {
                    'name': s_name,
                    'expires': s_expires
                },
                'suggestions': []
            }

            if github_token:
                if 'github_login' in request.session:
                    response['github_login'] = request.session['github_login']
                else:
                    github_login = requests.get(
                        'http://api.github.com/user?access_token=%s' % github_token
                    ).json()['login']
                    response['github_login'] = github_login
                    # Save result in session to avoid additional requests
                    request.session['github_login'] = github_login

                if 'github_suggestions' in request.session:
                    response['suggestions'].extend(request.session['github_suggestions'])
                else:
                    github_suggestions = get_user_repos_github(github_token)
                    response['suggestions'].extend(github_suggestions)
                    # Save result in session to avoid additional requests
                    request.session['github_suggestions'] = github_suggestions

            if bitbucket_token:
                if 'bitbucket_login' in request.session:
                    response['bitbucket_login'] = request.session['bitbucket_login']
                else:
                    bitbucket_login = requests.get(
                        'http://api.bitbucket.org/2.0/user',
                        headers={'Authorization': 'Bearer %s' % bitbucket_token}
                    ).json()['username']
                    response['bitbucket_login'] = bitbucket_login
                    # Save result in session to avoid additional requests
                    request.session['bitbucket_login'] = bitbucket_login

                if 'bitbucket_suggestions' in request.session:
                    response['suggestions'].extend(request.session['bitbucket_suggestions'])
                else:
                    bitbucket_suggestions = get_user_repos_bitbucket(bitbucket_token)
                    response['suggestions'].extend(bitbucket_suggestions)
                    # Save result in session to avoid additional requests
                    request.session['bitbucket_suggestions'] = bitbucket_suggestions

            if gitlab_token:
                if 'gitlab_login' in request.session:
                    response['gitlab_login'] = request.session['gitlab_login']
                else:
                    gitlab_login = requests.get(
                        'http://gitlab.com/api/v4/user',
                        headers={'Authorization': 'Bearer %s' % gitlab_token}
                    ).json()['username']
                    response['gitlab_login'] = gitlab_login
                    # Save result in session to avoid additional requests
                    request.session['gitlab_login'] = gitlab_login

                if 'gitlab_suggestions' in request.session:
                    response['suggestions'].extend(request.session['gitlab_suggestions'])
                else:
                    gitlab_suggestions = get_user_repos_gitlab(gitlab_token)
                    response['suggestions'].extend(gitlab_suggestions)
                    # Save result in session to avoid additional requests
                    request.session['gitlab_suggestions'] = gitlab_suggestions

            # Remove http:// and https:// from suggestions for better looks
            for i, link in enumerate(response['suggestions']):
                if link.startswith('https://'):
                    response['suggestions'][i] = link[8:]
                elif link.startswith('http://'):
                    response['suggestions'][i] = link[7:]

        return JsonResponse(response)


class GithubAccessToken(APIView):

    def delete(self, request):
        request.user.profile.github_access_token = ''
        request.user.save()

        # Clear cached data
        if 'github_login' in request.session:
            del request.session['github_login']
        if 'github_suggestions' in request.session:
            del request.session['github_suggestions']

        return Response()

    def get(self, request):

        return JsonResponse(
            {'token_exists': bool(request.user.profile.github_access_token)}
        )


class BitbucketAccessToken(APIView):

    def delete(self, request):
        request.user.profile.bitbucket_refresh_token = ''
        request.user.save()

        # Clear cached username
        if 'bitbucket_login' in request.session:
            del request.session['bitbucket_login']
        if 'bitbucket_suggestions' in request.session:
            del request.session['bitbucket_suggestions']

        return Response()

    def get(self, request):

        return JsonResponse(
            {'token_exists': bool(request.user.profile.bitbucket_refresh_token)}
        )


class GitlabAccessToken(APIView):

    def delete(self, request):
        request.user.profile.gitlab_refresh_token = ''
        request.user.save()

        # Clear cached username
        if 'gitlab_login' in request.session:
            del request.session['gitlab_login']
        if 'gitlab_suggestions' in request.session:
            del request.session['gitlab_suggestions']

        return Response()

    def get(self, request):

        return JsonResponse(
            {'token_exists': bool(request.user.profile.gitlab_refresh_token)}
        )


def add_rewrite_rule(request):
    created_rule_msg = ''
    if request.method == 'POST':
        form = RewriteNameForm(request.POST)
        if form.is_valid():
            initial = form.cleaned_data['initial_name']
            rewritten = form.cleaned_data['rewritten_name']
            simplified = simplify_lic_name(initial)

            # Check existing rules
            with open(rewrite_rules_path) as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
                rewrite_rules = {row[0].decode('utf8'): row[1].decode('utf-8')
                                 for row in csvreader}

            if simplified in rewrite_rules:
                created_rule_msg = RULE_ALREADY_EXISTS_MSG.format(
                    simplified, rewritten, rewrite_rules[simplified])
            else:
                # Add new rule to csv file
                created_rule_msg = REWRITE_RULE_SUCCESS.format(simplified, rewritten)
                with open(rewrite_rules_path, 'a') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"')
                    csvwriter.writerow([simplified, rewritten])

                # If there is LicenseStatistic with old name, rename it
                try:
                    lic_stat = LicenseStatistic.objects.get(name=initial)
                    # Check if there is already another LicenseStatistic with rewritten name
                    # If yes, combine license counts
                    try:
                        lic_stat_rewritten = LicenseStatistic.objects.get(name=rewritten)
                        lic_stat_rewritten.count += lic_stat.count
                        lic_stat_rewritten.save()
                    except LicenseStatistic.DoesNotExist:
                        treat_as = treat_as_rules.get(simplified) or rewritten
                        LicenseStatistic.objects.create(name=rewritten,
                                                        treat_as=treat_as,
                                                        count=1)
                    # Delete old LicenseStatistic
                    lic_stat.delete()
                except LicenseStatistic.DoesNotExist:
                    pass

    return render(
        request, 'admin/rewrite_rules.html',
        {'form': RewriteNameForm(), 'created_rule_msg': created_rule_msg}
    )


def add_treat_as_rule(request):
    created_rule_msg = ''
    if request.method == 'POST':
        form = TreatAsNameForm(request.POST)
        if form.is_valid():
            initial = form.cleaned_data['initial_name']
            treat_as = form.cleaned_data['treat_as_name']
            simplified = simplify_lic_name(initial)

            # Check existing rules
            with open(treat_as_rules_path) as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
                treat_as_rules = {row[0].decode('utf8'): row[1].decode('utf-8')
                                  for row in csvreader}

            if simplified in treat_as_rules:
                created_rule_msg = RULE_ALREADY_EXISTS_MSG.format(
                    simplified, treat_as, treat_as_rules[simplified])
            else:
                # Add new rule to csv file
                created_rule_msg = TREAT_AS_RULE_SUCCESS.format(simplified, treat_as)
                with open(treat_as_rules_path, 'a') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"')
                    csvwriter.writerow([simplified, treat_as])

                # If there is LicenseStatistic with initial name, change it's treat_as name
                try:
                    lic_stat = LicenseStatistic.objects.get(name=initial)
                    lic_stat.treat_as = treat_as
                    lic_stat.save()
                except LicenseStatistic.DoesNotExist:
                    pass

    return render(
        request, 'admin/treat_as_rules.html',
        {'form': TreatAsNameForm(), 'created_rule_msg': created_rule_msg}
    )
