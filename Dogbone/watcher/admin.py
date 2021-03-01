from django.contrib import admin

from watcher.models import (
    DropboxAccess,
    GoogleDriveAccess,
    Folder,
    Queue,
    Synchronized,
)


class CloudAccessAdmin(admin.ModelAdmin):
    list_display = ['user']
    readonly_fields = ['created', 'modified']


class DropboxAccessAdmin(CloudAccessAdmin):
    pass


class GoogleDriveAccessAdmin(CloudAccessAdmin):
    pass


class FolderAdmin(admin.ModelAdmin):
    list_display = ['title', 'cloud', 'user']
    readonly_fields = ['created', 'modified']


class QueueAdmin(admin.ModelAdmin):
    list_display = ['title', 'folder']
    readonly_fields = ['created', 'modified']


class SyncronizedAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'folder']
    readonly_fields = ['created', 'modified']


admin.site.register(DropboxAccess, DropboxAccessAdmin)
admin.site.register(GoogleDriveAccess, GoogleDriveAccessAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(Queue, QueueAdmin)
admin.site.register(Synchronized, SyncronizedAdmin)
