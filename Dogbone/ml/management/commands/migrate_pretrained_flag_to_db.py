from django.core.management.base import BaseCommand
from ml.models import OnlineLearner, PretrainedLearner


class Command(BaseCommand):
    help = ('Updates the existing OnlineLearner objects, setting the newly'
            'introduced pretrained flag')

    def handle(self, *args, **options):
        for ol in OnlineLearner.objects.all():
            pretrained_flag = PretrainedLearner.objects.filter(tag=ol.tag).exists()
            ol.pretrained = pretrained_flag
            ol.save()
