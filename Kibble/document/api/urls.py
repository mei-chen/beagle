from django.conf.urls import url, include
from document.api.router import document_router

urlpatterns = [
    url(r'^v1/', include(document_router.urls)),
]
