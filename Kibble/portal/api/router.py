from rest_framework.routers import DefaultRouter
from portal.api.viewsets import (
    BatchAPI, FileAPI, ProjectAPI, UserAPI, DogboneAPI
)

portal_router = DefaultRouter()

portal_router.register('batch', BatchAPI)
portal_router.register('file', FileAPI)
portal_router.register('project', ProjectAPI)
portal_router.register('user', UserAPI)

portal_router.register('dogbone', DogboneAPI, basename='dogbone')
