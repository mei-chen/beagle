from string import ascii_lowercase

from django.contrib import admin
from .models import SearchKeyword
from django.utils.translation import ugettext_lazy as _


class FirstLetterListFilter(admin.SimpleListFilter):
    title = _('First Letter')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'letter'

    def lookups(self, request, model_admin):
        return tuple([(letter, letter.upper()) for letter in ascii_lowercase])

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(keyword__startswith=self.value())

        return queryset


def activate(modeladmin, request, queryset):
    queryset.update(active=True)
activate.short_description = "Activate the item"


def deactivate(modeladmin, request, queryset):
    queryset.update(active=False)
deactivate.short_description = "Deactivate the item"


class SearchKeywordAdmin(admin.ModelAdmin):
    search_fields = ('owner__username', 'owner__email', 'owner__first_name', 'owner__last_name', 'keyword')
    list_filter = ('active', FirstLetterListFilter, 'created')
    list_display = ('keyword', 'owner', 'active', 'created', 'modified')
    actions = [activate, deactivate, ]

admin.site.register(SearchKeyword, SearchKeywordAdmin)