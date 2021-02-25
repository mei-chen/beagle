from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^interface/(?P<uuid>[a-z0-9\-]+)/$',
        views.interface_public,
        name='report_analysis_permalink'
    ),
    url(
        r'^user_details/',
        views.UserDetails.as_view(),
        name='user_details'
    ),
    url(
        r'^github_token/?',
        views.GithubAccessToken.as_view(),
        name='github_token'
    ),
    url(
        r'^bitbucket_token/?',
        views.BitbucketAccessToken.as_view(),
        name='bitbucket_token'
    ),
    url(
        r'^gitlab_token/?',
        views.GitlabAccessToken.as_view(),
        name='gitlab_token'
    ),

    # For react to work correctly
    url(
        r'^settings',
        views.index,
        name='settings'
    ),
    url(
        r'^history',
        views.index,
        name='history'
    ),
    url(
        r'^dashboard',
        views.index,
        name='dashboard'
    ),
    url(
        r'^report',
        views.index,
        name='report'
    ),
    url(
        r'^admin/add-rewrite-rule',
        views.add_rewrite_rule,
        name='add_rewrite_rule'
    ),
    url(
        r'^admin/add-treat-as-rule',
        views.add_treat_as_rule,
        name='add_treat_as_rule'
    ),
]
