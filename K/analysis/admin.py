from django.contrib import admin

from analysis.models import RegEx, Report, Keyword, KeywordList, SimModel


@admin.register(SimModel)
class SimModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'api_name', 'created_at']


@admin.register(RegEx)
class RegExAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'content', 'created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'report_type', 'created_at']


@admin.register(KeywordList)
class KeywordListAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['id', 'keyword_list', 'content', 'created_at']
