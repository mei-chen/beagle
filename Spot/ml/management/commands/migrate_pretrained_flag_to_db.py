from django.core.management.base import BaseCommand
from ml.models import OnlineLearner, PretrainedLearner


class Command(BaseCommand):
    help = ('Updates the existing OnlineLearner objects '
            'by properly setting the `pretrained` flag')

    def handle(self, *args, **options):
        for ol in OnlineLearner.objects.all():
            for pl in PretrainedLearner.objects.filter(tag=ol.tag):
                if pl.exclusivity and pl.exclusivity != ol.owner.username:
                    continue
                if not ol.pretrained:
                    ol.pretrained = True
                    ol.save()
                break
