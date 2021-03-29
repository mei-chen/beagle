if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from nlplib.utils import split_sentences, remove_linebreak_markers
from utils.conversion import filedecode
import fnmatch
import os
import time
import itertools
from unidecode import unidecode


wholetext = ''
fnames = []
toks = []
for root, dirnames, filenames in os.walk('resources'):
    for filename in fnmatch.filter(filenames, '*.txt'):
        fnames.append(filename)

        # wholetext += ' '
        text = filedecode(os.path.join(root, filename))
        # wholetext += ' ' + text
        # toks.extend(word_tokenize(text))
        curr_toks = list(map(remove_linebreak_markers,
                        split_sentences(unidecode(text))))
        for t in curr_toks:
            toks.extend([(filename, sent)
                         for sent in split_sentences(t)])

        # toks.extend(curr_toks)
        # print len(wholetext)

print len(toks)

import re
jurisdict = re.compile(
    r'(under\b.* the\b.* laws? of)|'
    r'(jurisdiction)|'
    r'(conflict of law)|'
    r'(conflicts of laws)|'
    r'(subject to the laws of)|'
    r'(govern)|'
    r'(court)|'
    r'(without\b.* regard)|'
    r'(in\b.* accordance.* with)|'
    r'(regulations)|'
    r'(authority)|'
    r'(exclusive)|'
    r'(territory)'
)

from beagle_bot.luis import LUIS

catches = []
for fname, t in toks:
    try:
        if jurisdict.search(t):
            matches = set(itertools.chain(*jurisdict.findall(t))) - set([''])
            print matches
            t = unidecode(t)
            highlighted = t
            for m in matches:
                highlighted = highlighted.replace(m, m.upper()).strip()

            # LUIS augmentation
            if len(matches) > 1:
                luis_api = LUIS(base_url='https://api.projectoxford.ai/luis/v1/application?id=8674f0a5-ad71-4318-a995-d089fe08697d&subscription-key=ec51008c54ec41aeb2d0197e847a175c')
                response = luis_api.generic_query(t)
            meaning = None
            subject = []
            if len(matches) > 1:
                try:
                    for i in response['intents']:
                        if i['intent'] == 'Jurisdiction clause':
                            meaning = i['score']
                    for e in response['entities']:
                        if e['type'] == 'Jurisdiction':
                            subject.append(e['entity'])
                except TypeError as e:
                    print e
                    print fname
                    print '- '*50
                    print t
                    meaning = '"Too Long" Error'
            subject = ', '.join(subject)

            catches.append((fname, highlighted, len(matches), meaning, subject, t.strip()))

            print '--- sleeping'
            time.sleep(0.2)
            print '--- /'
    except KeyboardInterrupt:
        break

import csv
with open('jurisdiction6.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"')
    header = ['Filename', 'Highlighted text', '# matches', 'LUIS score', 'LUIS subject', 'Original text']
    csvwriter.writerow(header)
    for r in catches:
        csvwriter.writerow(r)

for f in fnames:
    if f not in list(map(lambda x: x[0], catches)):
        print(f)
