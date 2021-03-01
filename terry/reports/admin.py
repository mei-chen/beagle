from django.contrib import admin

# Register your models here.
from reports.models import Report, ReportShared, LibStatistic, LicenseStatistic


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'url', 'user', 'created_at']


@admin.register(ReportShared)
class ReportSharedAdmin(admin.ModelAdmin):
    list_display = ['id', 'token', 'user', 'share_url', 'created_at']


@admin.register(LibStatistic)
class LibStatisticAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'licenses', 'package_manager', 'count']
    search_fields = ['name', 'licenses']


@admin.register(LicenseStatistic)
class LicenseStatisticAdmin(admin.ModelAdmin):
    list_display = ['name', 'treat_as', 'count']
    search_fields = ['name', 'treat_as']
