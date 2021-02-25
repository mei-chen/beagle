from django.conf.urls import url

from experiment.api.router import router
from experiment.api.views import (
    ValidateRegex,
    ExportPredicted,
    DiffPredicted,
    TrainClassifier,
    PlotClassifierDecisionFunction,
)


urlpatterns = router.urls

urlpatterns.append(
    url(
        r'^validate_regex/?$',
        ValidateRegex.as_view(),
        name='validate_regex'
    )
)

urlpatterns.append(
    url(
        r'^export_predicted/(?P<experiment_pk>\d+)/?$',
        ExportPredicted.as_view(),
        name='export_predicted'
    )
)

urlpatterns.append(
    url(
        r'^diff_predicted/(?P<experiment_pk>\d+)/?$',
        DiffPredicted.as_view(),
        name='diff_predicted'
    )
)

urlpatterns.append(
    url(
        r'^train_classifier/?$',
        TrainClassifier.as_view(),
        name='train_classifier'
    )
)

urlpatterns.append(
    url(
        r'^plot_classifier_decision_function/(?P<clf_uuid>[a-z0-9\-]+)/?$',
        PlotClassifierDecisionFunction.as_view(),
        name='plot_classifier_decision_function'
    )
)
