from django.core.management.base import BaseCommand
from django.conf import settings
from ml.models import OnlineLearner


class Command(BaseCommand):
    help = 'Moves the db field `model_uuid` to `model_s3` format. No actual file is moved ' \
           'The model_uuid is just a string uuid. The serialized model file is computed using: model_{UUID}.pkl' \
           '`model_s3` is an actual S3 path'

    def handle(self, *args, **options):
        for ol in OnlineLearner.objects.all():
            try:
                file_name = "model_%s.pkl" % ol.model_uuid
                ol.model_s3 = "%s:online_learners/%s" % (settings.PREDICTION_MODELS_BUCKET, file_name)
                ol.save()
                self.stdout.write('[*] migrated model=%s belonging to user=%s' % (ol.model_uuid, ol.owner))
            except:
                pass