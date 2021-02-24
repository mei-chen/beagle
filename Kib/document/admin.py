from django.conf import settings
from django.contrib import admin
from django.template.defaultfilters import truncatechars

# Register your models here.
from .models import (
    Document, DocumentTag, Sentence, PersonalData, CustomPersonalData
)


class SentenceInline(admin.TabularInline):
    model = Sentence
    classes = ['collapse']


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'text_preview', 'document']

    def text_preview(self, obj):
        return truncatechars(obj.text, settings.SENTENCE_PREVIEW_LENGTH)

    text_preview.admin_order_field = 'text'

    ordering = ['-id']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    inlines = [
        SentenceInline
    ]


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'name', 'created_at']


@admin.register(PersonalData)
class PersonalDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'batch', 'document', 'type',
                    'text', 'location', 'selected']


@admin.register(CustomPersonalData)
class CustomPersonalDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'text', 'selected']
