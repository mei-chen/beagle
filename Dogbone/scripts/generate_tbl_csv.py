'''
Generates a CSV with every clause in a given contract (see CONTRACT_PATH),
without annotations - ToBeLabeled format.
'''


if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from nlplib.utils import remove_linebreak_markers
from nlplib.facade import NlplibFacade
from utils.conversion import filedecode
from richtext.importing import parse_docx
from nlplib.utils import split_sentences
import fnmatch
import os
import time
import itertools
from unidecode import unidecode
import csv
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.settings'


CONTRACTS_ROOT = '/Users/iuliux/dogbone/resources'
CONTRACT_PATH = 'downloaded'
# CONTRACT_PATH = 'agreements'
fname = CONTRACT_PATH.split('/')[-1]

number_re = re.compile(r'\b([0-9]+[,.]?)+\b')
underscore_re = re.compile(r'\b(_+)\b')

rows = []
already_seen = set()
for root, dirnames, filenames in os.walk(os.path.join(CONTRACTS_ROOT, CONTRACT_PATH)):
    for filename in fnmatch.filter(filenames, '*.docx'):
    # for filename in fnmatch.filter(filenames, '*.txt'):
        try:
            print filename
            xmlsents = parse_docx(os.path.join(CONTRACTS_ROOT, CONTRACT_PATH, filename))
            sents = list(map(lambda x: unidecode(x), xmlsents[0]))
            # plaintext = filedecode(os.path.join(root, filename))
            # sents = split_sentences(unidecode(plaintext))

            content = '\n\n'.join(sents)
            plaintext = content

            fcd = NlplibFacade(text=plaintext)
            them_party, you_party, confidence = fcd.parties
            print '   ', them_party, you_party

            # terms = fcd.terminations(you_party)
            # terms.update(fcd.terminations(them_party))
            # terms.update(fcd.terminations('both'))

            # for k in terms:
            #     clause = unidecode(remove_linebreak_markers(fcd.sentences[k]))
            #     print clause
            #     masked_clause = number_re.sub('__NUM__', clause).strip()
            #     if masked_clause not in already_seen:
            #         rows.append((them_party, you_party, clause, '', ''))
            #         already_seen.add(masked_clause)

            for cl in sents:
                clause = remove_linebreak_markers(cl)
                masked_clause = number_re.sub(' __NUM_MASK__ ', clause)
                masked_clause = underscore_re.sub(' _ ', masked_clause).strip()  # Abstract fill-in lines
                if masked_clause not in already_seen:
                    rows.append((them_party, you_party, clause, '', ''))
                    already_seen.add(masked_clause)


            print('       ', len(rows))
            print()

        except KeyboardInterrupt:
            break

# criteria_re = re.compile(r'(\btermina|\bcancel\b|\bexit\b|\bsuspend|\bfinish|\bends?\b|\bnotice\b|\bconcludes?\b|\bcompletes?\b|\bquits?\b|\bwithdraws?\b|\bremoves?\b|\bleaves?\b|\bdeparts?\b|\bdiscontinues?\b|\bresigns?\b|\bstops?\b)', re.IGNORECASE)
criteria_re = re.compile(r'(\bresponsib|\bwill\b|\bmust\b|\bshall\b)', re.IGNORECASE)
from random import random

true_matches = 0
total = 0
with open('datasets/%s_responsibility_TBL.csv' % fname, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                           quotechar='"')
    header = ['THEM', 'YOU', 'CLAUSE', 'LABEL', 'PARTY', '']
    csvwriter.writerow(header)
    for r in sorted(rows, key=lambda x: len(x[2])):
        # csvwriter.writerow(r)
        if criteria_re.search(r[2]) or random() < .1:
            csvwriter.writerow(r)
            total += 1
            if criteria_re.search(r[2]):
                true_matches += 1
print
print true_matches, '/', total
