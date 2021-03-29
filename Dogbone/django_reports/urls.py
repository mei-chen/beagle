from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.report_list, name='django_reports.list'),
    url(r'^details/(?P<module_name>[a-zA-Z_0-9\.]+)/(?P<class_name>[a-zA-Z_0-9\.]+)$',
        views.report_details, name='django_reports.details'),
    url(r'^download/(?P<report_id>[0-9]+)$',
        views.report_download, name='django_reports.download'),
]
