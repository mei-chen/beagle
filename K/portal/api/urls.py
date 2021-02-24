from django.conf.urls import url, include

from portal.api.router import portal_router
from portal.api.views import ProfileAPI


urlpatterns = [
    url(r'^v1/', include(portal_router.urls)),

    url(r'^v1/profile/', ProfileAPI.as_view(), name='profile')
]
