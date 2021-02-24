from django.contrib import admin

# Register your models here.
from .models import Detail


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'env',
        'email_domain', 'endpoint_protocol',
        'endpoint_domain', 'created_at'
    ]
