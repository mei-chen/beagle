# App
from dataset.api import viewsets

# REST framework
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

router = DefaultRouter()

router.register(
    r'dataset',
    viewsets.DatasetViewSet,
    basename='dataset'
)

dataset_router = NestedSimpleRouter(
    router,
    r'dataset',
    lookup='dataset'
)

dataset_router.register(
    r'sample',
    viewsets.SampleViewSet,
    basename='sample'
)

router.register(
    r'labeling_task',
    viewsets.LabelingTaskViewSet,
    basename='labeling_task'
)

router.register(
    r'assignment',
    viewsets.AssignmentViewSet,
    basename='assignment'
)
