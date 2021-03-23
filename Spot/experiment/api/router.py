# App
from experiment.api import viewsets

# REST framework
from rest_framework import routers

router = routers.DefaultRouter()

router.register(
    r'experiment',
    viewsets.ExperimentViewSet,
    basename='experiment'
)

router.register(
    r'dogbone',
    viewsets.DogboneViewSet,
    basename='dogbone'
)

router.register(
    r'publish',
    viewsets.PublishViewSet,
    basename='publish'
)

router.register(
    r'online_learner',
    viewsets.OnlineLearnerViewSet,
    basename='online_learner'
)

router.register(
    r'formula',
    viewsets.FormulaViewSet,
    basename='formula'
)
