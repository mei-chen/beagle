from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'debug$', views.debug, name='realtime_debug'),
]