'''
Generates a CSV dataset (ToBeLabeled format) with clauses that match a regex
pattern from the whole contracts repository.
'''

if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from nlplib.utils import remove_linebreak_markers
from nlplib.facade import NlplibFacade
from utils.conversion import filedecode
import fnmatch
import os
import time
import itertools
from unidecode import unidecode
import csv
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.settings'

fnames = []
contracts = []
for root, dirnames, filenames in os.walk('resources'):
    for filename in fnmatch.filter(filenames, '*.txt'):
        fnames.append(filename)

        text = filedecode(os.path.join(root, filename))
        curr_content = unidecode(text)
        contracts.append((filename, curr_content))

print len(contracts)

pattern_re = re.compile(r'\bwill\b|\bshall\b|\bmust\b')

# Gather already listed clauses to avoid duplicates
already_extracted = set()
with open('datasets/extracted_TBL.csv', 'r') as csvin:
    csvreader = csv.reader(csvin, delimiter=',',
                           quotechar='"')
    for row in csvreader:
        already_extracted.add(row[2])


rows = []
for fname, contr in contracts:
    print fname
    try:
        fcd = NlplibFacade(text=contr)
        them_party, you_party, confidence = fcd.parties
        print '   ', them_party, you_party


        before = len(rows)

        rows.extend([(them_party, you_party, remove_linebreak_markers(clause), '', '', '', '')
                     for clause in fcd.processed_text
                     if clause not in already_extracted and pattern_re.search(clause.lower())])

        print '       ', (len(rows) - before)

    except KeyboardInterrupt:
        break

with open('datasets/patternmatched.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                           quotechar='"')
    header = ['THEM party', 'YOU party', 'CLAUSE', 'RESPONSIBILITY? (Y/N)', 'YOURS? (Y/N)', 'THEIRS? (Y/N)', 'NEGATED? (Y/N)']
    csvwriter.writerow(header)
    for r in rows:
        csvwriter.writerow(r)
