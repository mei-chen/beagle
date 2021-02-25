"""kibble URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from document.views import test_easypdf_view

# Use separate namespaces (where necessary)
# in order to eliminate any possible collisions
urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^', include('portal.urls', namespace='portal')),
    url(r'^document/', include('document.urls', namespace='document')),
    url(r'^reports/', include('analysis.urls', namespace='reports')),

    # API
    url(r'^api/', include('portal.api.urls')),
    url(r'^api/', include('document.api.urls')),
    url(r'^api/', include('analysis.api.urls')),
    url(r'^api/', include('watcher.api.urls')),

    # Third Party
    url(r'^accounts/', include('allauth.urls')),
    url(r'^watchman/', include('watchman.urls', namespace='watchman')),

    url(r'^test_easy_pdf/$', test_easypdf_view, name='test_easy_pdf'),

]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
