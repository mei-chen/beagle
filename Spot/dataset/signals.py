import django.dispatch

from dataset.models import Dataset
from experiment.models import make_trained_classifiers_dirty


sample_added = django.dispatch.Signal(providing_args=['sender', 'instance'])
sample_changed = django.dispatch.Signal(providing_args=['sender', 'instance'])
sample_removed = django.dispatch.Signal(providing_args=['sender', 'instance'])


sample_added.connect(receiver=make_trained_classifiers_dirty, sender=Dataset)
sample_changed.connect(receiver=make_trained_classifiers_dirty, sender=Dataset)
sample_removed.connect(receiver=make_trained_classifiers_dirty, sender=Dataset)
