from django.contrib import admin

# Register your models here.
from .models import User, Attachment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'email', 'success',
         'domain', 'created_at'
    ]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'document', 'created_at'
    ]
