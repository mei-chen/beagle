from django.contrib import admin
from .models import GeneratedReport
from django.core.urlresolvers import reverse


class GeneratedReportAdmin(admin.ModelAdmin):
    list_filter = ('created', )
    search_fields = ('title', )
    list_display = ('title', 'author', 'created', 'download_url')
    readonly_fields = ('params', 'author', )
    list_per_page = 20
    exclude = ('data', )

    def download_url(self, obj):
        download_url = reverse('django_reports.download', kwargs={'report_id': obj.pk})
        return '<a href="%s">%s</a>' % (download_url, 'Download')

    download_url.allow_tags = True

admin.site.register(GeneratedReport, GeneratedReportAdmin)