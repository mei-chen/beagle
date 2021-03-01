from django.conf.urls import url, include
from rest_framework import routers
from reports import views

router = routers.DefaultRouter()
router.register('reports', views.ReportViewSet)
router.register(r'permalinks', views.ReportSharedViewSet)
router.register(r'license_details', views.LicenseStatisticViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'pdf/(?P<report_uuid>[^/]+)/$', views.report_as_pdf, name='report_pdf'),
]
