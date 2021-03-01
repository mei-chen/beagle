from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'/debug$', 'beagle_realtime.views.debug', name='realtime_debug'),
)