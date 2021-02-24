# encoding=utf8

from __future__ import unicode_literals

from __future__ import print_function, unicode_literals, division
import io
import bz2
import logging
from toolz import partition,partition_all
from os import path
import os
import sys
import re
from unidecode import unidecode
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
import spacy.en
from preshed.counter import PreshCounter
from spacy.tokens.doc import Doc
import time
from joblib import Parallel, delayed
import plac


try:
    import ujson as json
except ImportError:
    import json

from tools import  joinUppercaseWords


nlp = spacy.load('en')
nlp.matcher = None
punkt_param=PunktParameters()
tokenizer=PunktSentenceTokenizer(punkt_param)

LABELS = {
    'ENT': 'ENT',
    'PERSON': 'PERSONT',
    'NORP': 'NORP',
    'FAC': 'FAC',
    'ORG': 'ORG',
    'GPE': 'GPE',
    'LOC': 'LOC',
    'LAW': 'LAW',
    'PRODUCT': 'PRODUCT',
    'EVENT': 'EVENT',
    'WORK_OF_ART': 'WORK_OF_ART',
    'LANGUAGE': 'LANGUAGE',
    'DATE': 'DATE',
    'TIME': 'TIME',
    'PERCENT': 'PERCENT',
    'MONEY': 'MONEY',
    'QUANTITY': 'QUANTITY',
    'ORDINAL': 'ORDINAL',
    'CARDINAL': 'CARDINAL'
}


def parallelize(func, iterator, n_jobs, extra):
    extra = tuple(extra)
    return Parallel(n_jobs=n_jobs)(delayed(func)(*(item + extra)) for item in iterator)


def to_unicode(strOrUnicode, encoding='utf-8'):
    '''Returns unicode from either string or unicode object'''
    if isinstance(strOrUnicode, unicode):
        return strOrUnicode
    return unicode(strOrUnicode, encoding, errors='ignore')


def get_file_names(dir_name):
    list_of_files=[]
    for root, subdirs, file_names in os.walk(dir_name):
        for file_name in file_names:
            if "DS_Store" not in file_name:  # For Mac ONLY
                filePath = os.path.join(root, file_name)
                list_of_files.append(filePath)
    return list_of_files

def iter_comments(dir_name):
    list_of_files=get_file_names(dir_name)
    temp=[]
    for file_name in list_of_files:
        try:
            with io.open(file_name, 'r',encoding='utf16') as f:
                string = ''.join(to_unicode(line.rstrip().replace(":",": ").replace(")",") "),encoding='utf-8') for line in f)
                temp.append(string.strip())
        except:
            with io.open(file_name, 'r') as f:
                for line in f:
                    if line.rstrip().replace('\n',''):
                        string = ''.join(to_unicode(line.rstrip().replace(":",": ").replace(")",") "),encoding='utf-8'))
                        temp.append(string.strip())
    return temp


def Convert_word(word):
    text = word.text
    # if word.prob < word.doc.vocab[text.lower()].prob:
    #      text = text.lower()
    return text



def pre_process(text):
    # nlp = spacy.load('en')
    sentences=tokenizer.tokenize(text)
    newText=[]
    for sent in sentences:
        sentence1 = ""
        doc = nlp(sent)
        sentence1 = ' '.join(Convert_word(w) for w in doc if not w.is_space)
        newText.append(sentence1)
    text='. '.join(sen for sen in newText if sen)
    return text.strip()

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def strip_meta(text):
    text = '  '.join(w for w in text.split() if (not hasNumbers(w)) and len(w)>1)
    text=text.replace("•",'').replace("}",")")
    text = text.replace("..", '')
    text = text.replace("..", '.')
    text=text.replace('_',' ')
    text=text.replace("\""," ")
    text = text.replace("\'", " ")
    return text

def parse_and_transform(batch_id, input_, out_dir):
    print("parsing...")
    out_loc = path.join(out_dir, '%d.txt' % batch_id)
    if path.exists(out_loc):
        return None
    print('Batch', batch_id)
    with io.open(out_loc, 'w', encoding='utf8') as file_:
        for text in input_:
            if text.strip:
                text = pre_process(strip_meta(text))
                try:
                        doc=nlp(text)
                        for sent in doc.sents:
                            file_.write(transform_doc(doc))
                except Exception, e:
                    continue

def transform_doc(doc):
    for ent in doc.ents:
        ent.merge(ent.root.tag_, ent.text, LABELS[ent.label_])
    for np in doc.noun_chunks:
        while len(np) > 1 and np[0].dep_ not in ('advmod', 'amod', 'compound'):
            np = np[1:]
        np.merge(np.root.tag_, np.text, np.root.ent_type_)

    strings = []
    for sent in doc.sents:
        if sent.text.strip():
            strings.append(' '.join(represent_word(w) for w in sent if not w.is_space))
    if strings:
        return '\n'.join(strings) + '\n'
    else:
        return ''


def represent_word(word):
    if word.like_url:
        return '%%URL|X'
    text = re.sub(r'\s', '_', word.text)
    tag = LABELS.get(word.ent_type_, word.pos_)
    if not tag:
        tag = '?'
    if tag not in ('PUNCT',"X") and len(text)>1:
        return text + '|' + tag
    else:
        return ''

@plac.annotations(
    in_loc=("Location of input file"),
    out_dir=("Location of output file"),
    n_CPUs=("Number of workers", "option", "n", int),
)
def main(in_loc, out_dir, n_CPUs=32):
    jobs = partition_all(500, iter_comments(in_loc))
    do_work = parse_and_transform
    parallelize(do_work, enumerate(jobs), n_CPUs, [out_dir])

if __name__ == '__main__':
    print("start parsing files")
    start_time = time.time()
    plac.call(main)
    print("end parsing files")
    print("--- %s seconds ---" % (time.time() - start_time))


