from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models
from django.forms import TextInput

from .models import (
    MAX_TOKEN_VALUE_LENGTH,
    AccessToken,
    ProjectCollaborationInvite,
    BatchCollaborationInvite,
)


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('last_login', 'date_joined')
    ordering = ('-date_joined',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ['value', 'owner']
    raw_id_fields = ['owner']

    formfield_overrides = {
        models.CharField: {
            'widget': TextInput(attrs={'size': MAX_TOKEN_VALUE_LENGTH})
        }
    }


class CollaborationInviteAdmin(admin.ModelAdmin):

    @property
    def target(self):
        raise NotImplementedError

    list_display = ['invitee', 'inviter']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['invitee', 'inviter']

    def __init__(self, *args, **kwargs):
        self.list_display = ['id', self.target] + self.list_display
        self.raw_id_fields = [self.target] + self.raw_id_fields

        super(CollaborationInviteAdmin, self).__init__(*args, **kwargs)


@admin.register(ProjectCollaborationInvite)
class ProjectCollaborationInviteAdmin(CollaborationInviteAdmin):

    @property
    def target(cls):
        return 'project'


@admin.register(BatchCollaborationInvite)
class BatchCollaborationInviteAdmin(CollaborationInviteAdmin):

    @property
    def target(cls):
        return 'batch'
