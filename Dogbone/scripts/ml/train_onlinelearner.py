import os
import sys

if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.settings'
os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.beta_settings'

from ml.facade import LearnerFacade
from ml.capsules import Capsule
from django.contrib.auth.models import User


from ml.resources.online import JURISDICTION_DATASET_PARTYMASKED

username = 'cian'
# username = 'iulius'
tag = 'Jurisdiction'
dataset = JURISDICTION_DATASET_PARTYMASKED

if len(sys.argv) < 1:
    print 'Usage: python scripts/ml/train_onlinelearner.py'

print 'Getting the object for %s/%s' % (username, tag)

user = User.objects.get(username=username)
clf = LearnerFacade.get_or_create(tag, user)

print 'Training Online Learner for <%s>' % clf.db_model.tag

import random
random.shuffle(dataset)
thresh = int(0.8 * len(dataset))

# --- Train ---
for i, (text, flags, label) in enumerate(dataset[:thresh]):
    if i and i % 25 == 0:
        print i
    clf.train([Capsule(text, flags=flags)], [label])

print 'Saving the ML model'
clf.ml_model.save_model()

print 'Saving the DB model'
clf.db_model.save()

# --- Evaluate ---
texts = [Capsule(text, flags=flags) for text, flags, _ in dataset[thresh:]]
gold = [label for _, _, label in dataset[thresh:]]
pred = clf.predict(texts)


from sklearn.metrics import f1_score, precision_score, recall_score
print 'Precision:', precision_score(gold, pred)
print 'Recall:   ', recall_score(gold, pred)
print 'F1 score: ', f1_score(gold, pred)


print 'Done!'
