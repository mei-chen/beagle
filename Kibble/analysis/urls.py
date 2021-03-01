from django.conf.urls import url
from analysis import views


urlpatterns = [
    url(
        r'^download-report/$',
        views.download_report,
        name='report_download'
    )
]
