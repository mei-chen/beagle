# import sys
# import  os
# import io
# import re
# import time
# import spacy
# import csv
# from operator import itemgetter
# from nltk.tokenize import word_tokenize,sent_tokenize
# import spacy

from spacy.lang.en import English

class sentenceTokenizer(object):

    def __init__(self):
        self.nlp = English()
        self.nlp.add_pipe("sentencizer")
    def __call__(self, text):

        return self.split_sentence(self.nlp,text)

    def split_sentence(self,nlp,text):
        sentences={}
        cleaned_text=' '.join(text.split())
        doc = self.nlp(cleaned_text)
        temp=[]
        for sent in doc.sents:
            temp.append(sent.text)
        sentences["sentences"] = temp

        return sentences



        # name=dict()
        # try:
        #     doc = nlp(sentence)
        # except Exception as e:
	    # print "nlp(sentence) Error = %s" % e
        #     try:
        #         doc = nlp(unicode(sentence.replace('NSW', 'New South Wales').replace(' the State of', ''), 'utf-8',errors='ignore'))
        #     except Exception as e:
		# print "nlp(unicode Error = %s" % e
        #         raise e
        # for ent in doc.ents:
        #     if ent.label_ not in name:
        #         name[ent.label_]=[]
        #         name[ent.label_].append(ent.text)
        #     else:
        #         name[ent.label_].append(ent.text)
        # return name

