from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models
from django.forms import TextInput
from django.shortcuts import reverse

from .models import (
    MAX_TOKEN_VALUE_LENGTH,
    AccessToken,
    DatasetCollaborationInvite,
    DatasetExternalInvite,
    ExperimentCollaborationInvite,
    ExperimentExternalInvite,
)


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Access token', {'fields': ('access_token_',)}),
    )
    readonly_fields = ('access_token_',)

    def access_token_(self, obj):
        try:
            token = obj.access_token
            url = reverse('admin:core_accesstoken_change', args=(token.id,))
            return '<a href="%s">%s</a>' % (url, token.value)
        except AccessToken.DoesNotExist:
            url = reverse('admin:core_accesstoken_add')
            return '<a href="%s">None</a>' % url

    access_token_.allow_tags = True
    access_token_.short_description = 'value'

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


@admin.register(DatasetCollaborationInvite)
class DatasetCollaborationInviteAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'invitee', 'inviter', 'created']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['dataset', 'invitee', 'inviter']


@admin.register(DatasetExternalInvite)
class DatasetExternalInviteAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'email', 'inviter', 'created']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['dataset', 'inviter']


@admin.register(ExperimentCollaborationInvite)
class ExperimentCollaborationInviteAdmin(admin.ModelAdmin):
    list_display = ['experiment', 'invitee', 'inviter', 'created']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['experiment', 'invitee', 'inviter']


@admin.register(ExperimentExternalInvite)
class ExperimentExternalInviteAdmin(admin.ModelAdmin):
    list_display = ['experiment', 'email', 'inviter', 'created']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['experiment', 'inviter']
