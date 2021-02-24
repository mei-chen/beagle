import sys
import  os
import io
import re
import time
import spacy
import csv
from operator import itemgetter
from nltk.tokenize import word_tokenize,sent_tokenize

import spacy

class nameEntities(object):

    def __init__(self, spacy_nlp):
        self.nlp = spacy_nlp

    def __call__(self, sentence):

        return self.nameExtract(self.nlp,sentence)

    def nameExtract(self,nlp,sentence):
        name=dict()
        try:
            doc = nlp(sentence)
        except Exception as e:
	    print "nlp(sentence) Error = %s" % e
            try:
                doc = nlp(unicode(sentence.replace('NSW', 'New South Wales').replace(' the State of', ''), 'utf-8',errors='ignore'))
            except Exception as e:
		print "nlp(unicode Error = %s" % e
                raise e
        for ent in doc.ents:
            if ent.label_ not in name:
                name[ent.label_]=[]
                name[ent.label_].append(ent.text)
            else:
                name[ent.label_].append(ent.text)
        return name

