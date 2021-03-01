import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ml.facade import LearnerFacade
from ml.models import OnlineLearner


class Command(BaseCommand):
    help = 'Adds new pretrained models to existing users'

    def handle(self, *args, **options):
        for u in User.objects.all():
            logging.info('Installing for user: %s (%s %s)' % (u.username,
                                                              u.first_name if u.first_name else None,
                                                              u.last_name if u.last_name else None))
            for pl in LearnerFacade.get_all(preload=False):
                if pl.db_model.exclusivity and pl.db_model.exclusivity != u.username:
                    continue

                if not OnlineLearner.objects.filter(tag=pl.db_model.tag, owner=u).exists():
                    logging.info('    Adding learner :: %s' % pl.db_model)
                    logging.getLogger().setLevel(40)
                    LearnerFacade.get_or_create(pl.db_model.tag, u, preload=False)
                    logging.getLogger().setLevel(10)
                else:
                    clf = OnlineLearner.objects.get(tag=pl.db_model.tag, owner=u)
                    clf.pretrained = True
                    clf.save()
