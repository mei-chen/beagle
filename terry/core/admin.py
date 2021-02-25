from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from core.models import Profile


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('date_joined',)
    ordering = ('-date_joined',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'github_access_token', 'bitbucket_refresh_token',
                    'gitlab_refresh_token']
