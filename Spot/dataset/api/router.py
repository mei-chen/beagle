# App
from dataset.api import viewsets

# REST framework
from rest_framework_nested import routers

router = routers.DefaultRouter()

router.register(
    r'dataset',
    viewsets.DatasetViewSet,
    base_name='dataset'
)

dataset_router = routers.NestedSimpleRouter(
    router,
    r'dataset',
    lookup='dataset'
)

dataset_router.register(
    r'sample',
    viewsets.SampleViewSet,
    base_name='sample'
)

router.register(
    r'labeling_task',
    viewsets.LabelingTaskViewSet,
    base_name='labeling_task'
)

router.register(
    r'assignment',
    viewsets.AssignmentViewSet,
    base_name='assignment'
)
