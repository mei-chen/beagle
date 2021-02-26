if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from nlplib.facade import NlplibFacade
import fnmatch
import os
import re
import csv
import time
import itertools
from collections import defaultdict
from unidecode import unidecode

os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.settings'


DATASET = 'datasets/terminations.csv'

data = defaultdict(list)
with open(DATASET, 'rb') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

    for row in csvreader:
        you = row[0]
        them = row[1]
        clause = row[2]
        label = row[3]
        party = row[4]

        data[(you, them)].append((clause, label, party))

global_gold = []
global_pred = []
global_sents = []
for ((you, them), d) in data.iteritems():
    print '--- ---', you, them, '--- ---'
    sents = map(lambda x: x[0], d)
    global_sents.extend(sents)
    fcd = NlplibFacade(parties=(them, you, None), sentences=sents)

    gold = map(lambda x: x[1].startswith('T'), d)
    pred = [False] * len(sents)
    
    terms = fcd.terminations(you)
    terms.update(fcd.terminations(them))
    terms.update(fcd.terminations('both'))
    for k in terms:
        pred[k] = True

    global_gold.extend(gold)
    global_pred.extend(pred)

    print terms
    print


from sklearn.metrics import precision_score, recall_score, f1_score

print 'Precision:', precision_score(global_gold, global_pred)
print 'Recall:   ', recall_score(global_gold, global_pred)
fscr = f1_score(global_gold, global_pred)
print 'F-score:  ', fscr

true_pos, true_neg, false_pos, false_neg = 0, 0, 0, 0

for i, (pred, gold) in enumerate(zip(global_pred, global_gold)):
    if pred:
        if gold:
            true_pos += 1
            # print global_sents[i]
        else:
            false_pos += 1
    else:
        if gold:
            false_neg += 1
        else:
            true_neg += 1

print 'True Pos:', true_pos
print 'True Neg:', true_neg
print 'False Pos:', false_pos
print 'False Neg:', false_neg
