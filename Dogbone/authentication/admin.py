from django.contrib import admin
from .models import AuthToken, PasswordResetRequest, OneTimeLoginHash


def refresh_token(model_admin, request, queryset):
    for item in queryset:
        item._regenerate()

refresh_token.short_description = "Refresh Token"


def make_permanent_token(model_admin, request, queryset):
    for item in queryset:
        item.make_permanent()

make_permanent_token.short_description = "Make Token Permanent"


class AuthTokenAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('token', 'user', 'expired', )
    search_fields = ('key', 'user__email', 'user__username')
    list_filter = ('created', )
    actions = [refresh_token, make_permanent_token]

    def token(self, obj):
        return obj.token

    def expired(self, obj):
        return obj.is_expired

admin.site.register(AuthToken, AuthTokenAdmin)


class PasswordResetRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(PasswordResetRequest, PasswordResetRequestAdmin)


class OneTimeLoginHashAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'login_hash', 'resolved')

    def login_hash(self, obj):
        return obj.get_hash()

admin.site.register(OneTimeLoginHash, OneTimeLoginHashAdmin)