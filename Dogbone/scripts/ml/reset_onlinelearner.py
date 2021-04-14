import os
import sys

if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.settings'

from ml.facade import LearnerFacade
from django.contrib.auth.models import User

if len(sys.argv) < 3:
    print 'Usage: python scripts/ml/reset_onlinelearner.py <tag> <user>'

print 'Getting the object for %s/%s' % (sys.argv[2], sys.argv[1])

user = User.objects.get(username=sys.argv[2])
clf = LearnerFacade.get_or_create(sys.argv[1], user)

print 'Resetting Online Learner for <%s>' % clf.db_model.tag

clf.ml_model.reset(initial_samples=list(zip(
    clf.db_model.samples['text'],
    clf.db_model.samples['flags'],
    clf.db_model.samples['label'],
)))

print 'Saving the ML model'

clf.ml_model.save_model()

print 'Done!'
