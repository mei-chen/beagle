import os
import re
import csv
import hashlib
from time import gmtime, strftime

if __package__ is None:
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

os.environ['DJANGO_SETTINGS_MODULE'] = 'dogbone.beta_settings'
from unidecode import unidecode
from core.models import Document
from nlplib.utils import markers_to_linebreaks


urlchars_re = re.compile(r'[:/\\]+')

doc_data = {}
already_hashed = set()
cur_day = strftime("%Y-%m-%d", gmtime())
results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'docs_%s' % cur_day)
if not os.path.exists(results_path):
    os.mkdir(results_path)

for doc in Document.objects.all():
    try:
        print
        print '---', unidecode(doc.original_name)
        filename = unidecode(doc.original_name)
        filename = filename.replace('.beagle', '')
        filename = os.path.splitext(filename)[0]
        filename = urlchars_re.sub('', filename)
        print '   ', filename
        if filename in doc_data:
            print '<Skip (duplicate)>'
            continue
        if not doc.doclevel_analysis:
            print 'Malformed document: %s, pk=%s' % (unidecode(doc.original_name), doc.pk)
            continue
        parties_data = doc.doclevel_analysis['parties']
        them = parties_data['them']['name']
        them_confidence = parties_data['them']['confidence']
        you = parties_data['you']['name']
        you_confidence = parties_data['you']['confidence']
        print unidecode(them), ' | ', unidecode(you)
        if them_confidence <= 100 and you_confidence <= 100:
            doc_data[filename] = {
                'Filename': filename,
                'Them': unidecode(them),
                'Them-confidence': them_confidence,
                'You': unidecode(you),
                'You-confidence': you_confidence,
            }
        # Check if content is duplicate
        doc_hash = hashlib.md5(unidecode(doc.raw_text)).hexdigest()
        print doc_hash
        if doc_hash in already_hashed:
            print '<Skip (duplicate content)>'
            continue
        already_hashed.add(doc_hash)

        filename = '%s.txt' % filename
        raw_text_path = os.path.join(results_path, filename)
        with open(raw_text_path, 'w') as writefile:
            text = markers_to_linebreaks(doc.raw_text)
            writefile.write(text.encode('utf-8'))
    except KeyboardInterrupt:
        break
    except:
        continue

csv_path = os.path.join(results_path, 'docs.csv')
with open(csv_path, 'w') as csvfile:
    fieldnames = ['Filename', 'Them', 'Them-confidence', 'You', 'You-confidence']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for doc in doc_data:
        writer.writerow(doc_data[doc])
