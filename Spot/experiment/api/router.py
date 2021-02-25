# App
from experiment.api import viewsets

# REST framework
from rest_framework import routers

router = routers.DefaultRouter()

router.register(
    r'experiment',
    viewsets.ExperimentViewSet,
    base_name='experiment'
)

router.register(
    r'dogbone',
    viewsets.DogboneViewSet,
    base_name='dogbone'
)

router.register(
    r'publish',
    viewsets.PublishViewSet,
    base_name='publish'
)

router.register(
    r'online_learner',
    viewsets.OnlineLearnerViewSet,
    base_name='online_learner'
)

router.register(
    r'formula',
    viewsets.FormulaViewSet,
    base_name='formula'
)
