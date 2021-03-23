"""spot URL Configuration

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
from django.conf.urls import url, include
from django.contrib import admin

from portal.views import EmailAutofillSignupView

# Use separate namespaces (where necessary)
# in order to eliminate any possible collisions
urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^', include(('portal.urls', 'portal'), namespace='portal')),

    # API
    url(r'^api/v1/', include(('dataset.api.urls', 'dataset.api'), namespace='dataset-api')),
    url(r'^api/v1/', include(('experiment.api.urls', 'experiment.api'), namespace='experiment-api')),

    # Third Party
    url(r'^accounts/signup/', EmailAutofillSignupView.as_view(), name='account_signup'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^watchman/', include(('watchman.urls', 'watchman'), namespace='watchman')),
]
