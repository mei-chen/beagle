if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import csv
import time

from beagle_bot.luis import LUIS


rows = []

# with open('scripts/jurisd_baseline.csv', 'r') as csvin:
with open('jurisdiction6_negatives.csv', 'r') as csvin:
    csvreader = csv.reader(csvin, delimiter=',',
                            quotechar='"')
    csvreader.next()
    for i, row in enumerate(csvreader):
        if i and i % 25 == 0:
            print i

        fname, hglt, nmc, orig_score, _, text, label = row

        # LUIS augmentation
        luis_api = LUIS(base_url='https://api.projectoxford.ai/luis/v1/application?id=8674f0a5-ad71-4318-a995-d089fe08697d&subscription-key=ec51008c54ec41aeb2d0197e847a175c')
        response = luis_api.generic_query(text)
        meaning = 0.
        nonescore = 0.
        subject = []
        try:
            for i in response['intents']:
                if i['intent'] == 'Jurisdiction clause':
                    meaning = i['score']
                if i['intent'] == 'None':
                    nonescore = i['score']
            for e in response['entities']:
                if e['type'] == 'Jurisdiction':
                    subject.append(e['entity'])
        except TypeError as e:
            print e
            print fname
            print '- '*50
            print text
            meaning = '"Too Long" Error'

        subject = ', '.join(subject)

        if meaning >= nonescore:
            predicted = 1
        else:
            predicted = 2

        rows.append((fname, hglt, nmc, orig_score, text, label, meaning, subject, predicted))
        time.sleep(0.2)


with open('jurisdiction_benchmark_negatives.csv', 'w') as csvout:
    csvwriter = csv.writer(csvout, delimiter=',',
                            quotechar='"')
    header = ['Filename', 'Highlighted text', '# matches', 'LUIS score before', 'Text', 'Manual label', 'LUIS score after', 'LUIS subject', 'Predicted label']
    csvwriter.writerow(header)
    for r in rows:
        csvwriter.writerow(r)