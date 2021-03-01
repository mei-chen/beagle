from django.contrib import admin

from utils.django_utils.admin_utils import DeleteWithoutConfirmationAdminMixin

from .models import Event


class EventAdmin(DeleteWithoutConfirmationAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'user',)
    readonly_fields = ('created', 'modified',)


admin.site.register(Event, EventAdmin)
