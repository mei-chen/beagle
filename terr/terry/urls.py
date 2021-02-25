"""terry URL Configuration

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
from django.contrib import admin
from django.views.static import serve

from portal.account_views import LoginViewCustom, SignupViewCustom

# Use separate namespaces (where necessary)
# in order to eliminate any possible collisions
urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^', include('portal.urls', namespace='portal')),

    # API
    url(r'^api/v1/', include('core.api.urls', namespace='core-api')),

    # Reports
    url(r'^api/v1/', include('reports.urls', namespace='reports-api')),

    # Marketing
    url(r'^marketing/', include('marketing.urls', namespace='marketing')),

    # Override some account views
    url(r'^accounts/login/$', LoginViewCustom.as_view(), name="account_login"),
    url('^accounts/social/signup/$', SignupViewCustom.as_view(), name='socialaccount_signup'),

    # Third Party
    url(r'^accounts/', include('allauth.urls')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^watchman/', include('watchman.urls', namespace='watchman')),

    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
]
