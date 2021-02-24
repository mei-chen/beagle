# encoding=utf8

from __future__ import unicode_literals

from __future__ import print_function, unicode_literals, division
import io
import bz2
import logging
from toolz import partition
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
import dill

try:
    import ujson as json
except ImportError:
    import json


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

def to_unicode(strOrUnicode, encoding='utf-8'):
    '''Returns unicode from either string or unicode object'''
    if isinstance(strOrUnicode, unicode):
        return strOrUnicode
    return unicode(strOrUnicode, encoding, errors='ignore')

def get_file_names(dir_name):

    list_of_files=[]
    file_names=next(os.walk(dir_name))[2]

    for file_name in file_names:
        if "DS_Store" not in file_name:  # For Mac ONLY
            list_of_files.append(sys.argv[1]+"/"+file_name)
    return list_of_files

def iter_comments(dir_name):
    list_of_files=get_file_names(dir_name)
    temp=[]
    for file_name in list_of_files:
        try:
            with io.open(file_name, 'r',encoding='utf16') as f:
                string = ''.join(to_unicode(line.rstrip(),encoding='utf-8') for line in f)
                temp.append(string)
        except:
            with io.open(file_name, 'r') as f:
                string = ''.join(to_unicode(line.rstrip(),encoding='utf-8') for line in f)
                temp.append(string)
    return temp

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

    print(text)

    return text

class BatchSpacy():

    def __init__(self,in_loc,out_dir,n_CPUs):
        """Return a Customer object whose name is *name* and starting
        balance is *balance*."""
        self.nlp = spacy.en.English()
        self.in_loc=in_loc
        self.out_dir=[out_dir]
        self.cpus=n_CPUs
        self.jobs = partition(5, iter_comments(self.in_loc))

    def parse_and_transform(self,input_, out_dir,batch_id):
        print("parsing...")
        out_loc = path.join(out_dir, '%d.txt' % batch_id)
        if path.exists(out_loc):
            return None
        print('Batch', batch_id)
        with io.open(out_loc, 'w', encoding='utf8') as file_:
            for text in input_:
                text = strip_meta(text)
                try:
                    file_.write(self.transform_doc(self.nlp(text)))
                except:
                    continue

    def transform_doc(self, doc):
        for ent in doc.ents:
            ent.merge(ent.root.tag_, ent.text, LABELS[ent.label_])
        for np in doc.noun_chunks:
            while len(np) > 1 and np[0].dep_ not in ('advmod', 'amod', 'compound'):
                np = np[1:]
            np.merge(np.root.tag_, np.text, np.root.ent_type_)
        strings = []
        for sent in doc.sents:
            if sent.text.strip():
                strings.append(' '.join(self.represent_word(w) for w in sent if not w.is_space))
        if strings:
            return '\n'.join(strings) + '\n'
        else:
            return ''

    def represent_word(self, word):
        if word.like_url:
            return '%%URL|X'
        text = re.sub(r'\s', '_', word.text)
        tag = LABELS.get(word.ent_type_, word.pos_)
        if not tag:
            tag = '?'
        if tag not in ('PUNCT', "X") and len(text) > 1:
            return text + '|' + tag
        else:
            return ''

    # def parallelize(self):
    #     extra = tuple(self.out_dir)
    #     return Parallel(n_jobs=self.cpus)(delayed(unwrap_self)(self.in_loc, self.out_dir, *(item + extra)) for item in enumerate(self.jobs))



@plac.annotations(
    in_loc=("Location of input file"),
    out_dir=("Location of output file"),
    n_CPUs=("Number of workers", "option", "n", int),
)
def main(in_loc, out_dir, n_CPUs=4):
    myBatchProcess=BatchSpacy(in_loc, out_dir,4)
    #myBatchProcess.parallelize()
    def unwrap_self(func,*args):
        return func(*args)
    extra = tuple(myBatchProcess.out_dir)
    Parallel(n_jobs=myBatchProcess.cpus)(delayed(unwrap_self)(myBatchProcess.parse_and_transform, myBatchProcess.in_loc, myBatchProcess.out_dir, *(item + extra)) for item in enumerate(myBatchProcess.jobs))

if __name__ == '__main__':

    print("start parsing files")
    start_time = time.time()
    plac.call(main)
    print("end parsing files")
    print("--- %s seconds ---" % (time.time() - start_time))

