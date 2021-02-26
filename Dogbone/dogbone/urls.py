import django_reports

from django.contrib import admin
from django.conf.urls import patterns, include, url

from marketing import action

admin.autodiscover()
django_reports.autodiscover()
action.autodiscover()

# Use separate namespaces (where necessary)
# in order to eliminate any possible collisions
urlpatterns = patterns('',
    url(r'^', include('portal.urls')),
    url(r'^adm/office/', include(admin.site.urls)),
    url(r'^realtime', include('beagle_realtime.urls')),
    url(r'^api/v1', include('api_v1.urls')),
    url(r'^reports/', include('django_reports.urls')),
    url(r'^payments/paypal/', include('paypal.standard.ipn.urls')),
    url(r'^watchman/', include('watchman.urls', namespace='watchman')),
)

handler404 = 'portal.views.error404'


# Make the dev server also serve Media files
from django.conf import settings
if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}))
