from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$',
        'django_reports.views.report_list', name='django_reports.list'),
    url(r'^details/(?P<module_name>[a-zA-Z_0-9\.]+)/(?P<class_name>[a-zA-Z_0-9\.]+)$',
        'django_reports.views.report_details', name='django_reports.details'),
    url(r'^download/(?P<report_id>[0-9]+)$',
        'django_reports.views.report_download', name='django_reports.download'),
)
