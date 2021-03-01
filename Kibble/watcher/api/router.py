from rest_framework.routers import DefaultRouter
from watcher.api.viewsets import CloudAuthAPI, CloudFolderAPI

watcher_router = DefaultRouter()
watcher_router.register(
    'cloud_auth', CloudAuthAPI, basename='cloud_auth'
)
watcher_router.register(
    'cloud_folder', CloudFolderAPI, basename='cloud_folder'
)
