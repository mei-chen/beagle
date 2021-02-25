from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ml.facade import LearnerFacade
from ml.models import OnlineLearner


class Command(BaseCommand):
    help = 'Adds new pretrained learners to existing users'

    def handle(self, *args, **options):
        # TODO: make sure to delete these lines as soon as possible
        print 'Not working yet!'
        return

        print
        print '=' * 80
        print

        for u in User.objects.order_by('username'):
            print 'Installing for user: %s' % u

            for pl in LearnerFacade.get_all(preload=False):
                if pl.db_model.exclusivity and pl.db_model.exclusivity != u.username:
                    continue

                tag = pl.db_model.tag
                if tag.startswith('trained#') or tag.startswith('builtin#'):
                    continue

                ol = OnlineLearner.objects.filter(tag=tag, owner=u).last()
                if not ol:
                    print '>>> Adding learner for tag: %s' % tag
                    LearnerFacade.get_or_create(tag, u, preload=False)
                elif not ol.pretrained:
                    ol.pretrained = True
                    ol.save()

            print
            print '=' * 80
            print
