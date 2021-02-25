# App
from core.api import viewsets

# rest_framework
from rest_framework import routers


router = routers.DefaultRouter()

router.register(
    r'licenses',
    viewsets.LicensesViewSet,
    base_name='licenses'
)

router.register(
    r'OAuthCallback',
    viewsets.OAuthCallbackViewSet,
    base_name='OAuthCallback'
)

router.register(
    r'GitHubApp',
    viewsets.GithubAppViewset,
    base_name='GitHubApp'
)
