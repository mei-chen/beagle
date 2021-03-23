from django.conf.urls import url

from portal import views

urlpatterns = [
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^user_details/?$',
        views.UserDetails.as_view(),
        name='user_details'
    ),

    # For react to work correctly
    url(
        r'^experiments/?$',
        views.index,
        name='index'
    ),
    url(
        r'^experiments/\d+/edit/?$',
        views.index,
        name='index'
    ),
    url(
        r'^experiments/\d+/evaluate/?$',
        views.index,
        name='index'
    ),
    url(
        r'^datasets/?',
        views.index,
        name='index'
    ),
    url(
        r'^datasets/\d+/?$',
        views.index,
        name='index'
    ),
    url(
        r'^create-experiment/?',
        views.index,
        name='index'
    ),
    url(
        r'^create-dataset/?',
        views.index,
        name='index'
    ),
    url(
        r'^tasks/?',
        views.index,
        name='index'
    ),
    url(
        r'^create-task/?',
        views.index,
        name='index'
    ),
    url(
        r'^assignments/?',
        views.index,
        name='index'
    ),
    url(
        r'^export-supervised-dataset/?',
        views.index,
        name='index'
    )
]
