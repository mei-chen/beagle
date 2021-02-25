from django.conf.urls import url, include

from watcher.api.router import watcher_router

urlpatterns = [
    url(r'^v1/', include(watcher_router.urls)),
]
