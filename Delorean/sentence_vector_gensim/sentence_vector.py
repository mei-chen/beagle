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


import gensim.downloader as api
import numpy as np


class sentenceVectorizer(object):

    def __init__(self):
        try:
            self.word2vec = api.load('glove-wiki-gigaword-100')
        except:
            print("no model")

    def __call__(self, sentences):

        return self.sentence_vectorize(self.word2vec,sentences)

    def sentence_vectorize(self,wv,sents):
        sent_vectors=[]
        for sent in sents:
            total=np.zeros(100)
            count_oov=0
            for word in sent.split():
                try:
                    total=total+np.array(wv[word]) #skip OOV words
                except:
                    count_oov =+1
                    pass
            vector=np.true_divide(total,len(sent.split())-count_oov)
            sent_vectors.append(vector.tolist())
        return {"vectors":sent_vectors}



        # print(wv['asparagus'])
        # sentences={}
        # sentences={}
        # cleaned_text=' '.join(text.split())
        # doc = self.nlp(cleaned_text)
        # temp=[]
        # for sent in doc.sents:
        #     temp.append(sent.text)
        # sentences["sentences"] = temp
        #
        # return sentences



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

