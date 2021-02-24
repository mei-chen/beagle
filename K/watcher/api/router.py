from rest_framework.routers import DefaultRouter
from viewsets import CloudAuthAPI, CloudFolderAPI

watcher_router = DefaultRouter()
watcher_router.register(
    'cloud_auth', CloudAuthAPI, base_name='cloud_auth'
)
watcher_router.register(
    'cloud_folder', CloudFolderAPI, base_name='cloud_folder'
)
