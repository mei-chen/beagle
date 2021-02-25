from django.conf.urls import url
import views


urlpatterns = [
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^user_details/',
        views.UserDetails.as_view(),
        name='user_details'
    ),
    url(
        r'^find_personal_data/',
        views.FindPersonalData.as_view(),
        name='find_personal_data'
    )
]
