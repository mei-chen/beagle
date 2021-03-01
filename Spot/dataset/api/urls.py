# App
from dataset.api.router import router, dataset_router

# Django
from django.conf.urls import url, include

urlpatterns = [
    url('^', include(router.urls)),
    url('^', include(dataset_router.urls)),
]
