from core.api.router import router
from django.conf.urls import url

import views

urlpatterns = router.urls

urlpatterns.append(
    url(r'^check_repo/',
        views.RepoDetails.as_view(),
        name='repo_details')
)
