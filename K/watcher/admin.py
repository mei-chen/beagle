from django.contrib import admin

from watcher.models import (
    DropboxAccess, GoogleDriveAccess,
    CloudFolder, CloudFile,
)


class CloudAccessAdmin(admin.ModelAdmin):
    list_display = ['user']


@admin.register(DropboxAccess)
class DropboxAccessAdmin(CloudAccessAdmin):
    pass


@admin.register(GoogleDriveAccess)
class GoogleDriveAccessAdmin(CloudAccessAdmin):
    pass


@admin.register(CloudFolder)
class CloudFolderAdmin(admin.ModelAdmin):
    list_display = ['folder_path', 'cloud', 'user']
    readonly_fields = ['created', 'modified']


@admin.register(CloudFile)
class CloudFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'folder']
    readonly_fields = ['created', 'modified']
