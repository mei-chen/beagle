from __future__ import unicode_literals, print_function
try:
    from urllib.parse import unquote
except ImportError:
    from urllib2 import unquote

# import ujson as json
import json
import spacy
# import sense2vec
# import numpy as np

from falcon_multipart.middleware import MultipartMiddleware


import falcon
from falcon_cors import CORS


from Sentence_splitting.sentence_splitting import sentenceTokenizer
from sentence_vector_gensim.sentence_vector import sentenceVectorizer

from sense2vec_service_word.modelSelection import load_models
from sense2vec_service_word.similarity import Similarity, Similarity_GoogleNews
#
# from sense2vec_service_word.similarity import SimilarityScore_wiki_300,SimilarityScore_GoogleNews_300,SimilarityScore, SimilarityScore_FWCA_300,SimilarityScore_FWCA_200,SimilarityScore_FWCA_128,SimilarityScore_EUlaw_300,SimilarityScore_EUlaw_128,SimilarityScore_EUlaw_200,SimilarityScore_FWCA_plain_128,SimilarityScore_FWCA_plain_200,SimilarityScore_FWCA_plain_300
#
# from partyIdentifier_nda.nda_parties import partyIdentifier
#
# from DefinitionTools.extractDefintions import definitions
# from NameEntities.nameEntities import nameEntities

#from textGeneration.TextGeneration import  TextGeneration


class SimilarityService(object):
    '''Expose a sense2vec handler as a GET service for falcon.'''
    def __init__(self):
        google_news, eu_law, us_law=load_models()
        self.handler_GoogleNews = Similarity_GoogleNews(google_news)
        self.handler_EUlaw = Similarity(spacy.load("en_core_web_sm"),eu_law)
        self.handler_USlaw = Similarity(spacy.load("en_core_web_sm"),us_law)

    def on_get(self, req, resp, word='',model='us_law',number=10):

        if model=='googlenews':
            resp.media = json.dumps(self.handler_GoogleNews(word))
        if model=='eulaw':
            resp.media = json.dumps(self.handler_EUlaw(word))
        if model == 'lawinsider':
            resp.media = json.dumps(self.handler_USlaw(word))

# class SimilarityScoreService(object):
#     '''Expose a sense2vec handler as a GET service for falcon.'''
#     def __init__(self):
#         self.handler_default = SimilarityScore(
#             spacy.load('en', parser=False, entity=False),
#             sense2vec.load())
#
#         self.handler_FWCA_300 = SimilarityScore_FWCA_300(
#             spacy.load('en', parser=False, entity=False),
#             load_FWCA_300())
#
#         self.handler_FWCA_200 = SimilarityScore_FWCA_200(
#             spacy.load('en', parser=False, entity=False),
#             load_FWCA_200())
#
#         self.handler_FWCA_128 = SimilarityScore_FWCA_128(
#             spacy.load('en', parser=False, entity=False),
#             load_FWCA_128())
#
#         self.handler_FWCA_plain_128 = SimilarityScore_FWCA_plain_128(
#             load_FWCA_plain_128())
#
#         self.handler_FWCA_plain_200 = SimilarityScore_FWCA_plain_200(
#             load_FWCA_plain_200())
#
#         self.handler_FWCA_plain_300 = SimilarityScore_FWCA_plain_300(
#             load_FWCA_plain_300())
#
#         self.handler_EUlaw_300 = SimilarityScore_EUlaw_300(
#             spacy.load('en', parser=False, entity=False),
#             load_EUlaw_300())
#
#         self.handler_EUlaw_128 = SimilarityScore_EUlaw_128(
#             spacy.load('en', parser=False, entity=False),
#             load_EUlaw_128())
#
#         self.handler_EUlaw_200 = SimilarityScore_EUlaw_200(
#             spacy.load('en', parser=False, entity=False),
#             load_EUlaw_200())
#
#         self.handler_wiki_300 = SimilarityScore_wiki_300(
#             load_wiki_300())
#
#         self.handler_GoogleNews_300 = SimilarityScore_GoogleNews_300(
#             load_GoogleNews_300())
#
#     def on_get(self, req, resp, query=''):
#         query1=query.split("&")
#         newquery={}
#         newquery["word1"]=''
#         newquery["model"]='default'
#         newquery["word2"] = ''
#         newquery['user'] = ''
#         newquery['password'] = ''
#         for each in query1:
#             try:
#                 if each.split("=")[0]=='word1':
#                     newquery["word1"] = each.split("=")[1]
#                 if each.split("=")[0] == 'model':
#                    newquery["model"] = each.split("=")[1]
#                 if each.split("=")[0] == 'word2':
#                    newquery["word2"] = each.split("=")[1]
#                 try:
#                     if each.split("=")[0]=='user':
#                         newquery["user"] = each.split("=")[1]
#                     if each.split("=")[0]=='password':
#                         newquery["password"] = each.split("=")[1]
#                 except:
#                     resp.body = ('\n Provide user and password.')
#             except:
#                 resp.body = ('\n Provide correct query.\n''\n''    ~ Beagle Inc.\n\n')
#         if newquery["user"] != 'Beagle' or newquery["password"] != 'GreatBeagleAI':
#             resp.body = ('\n Provide correct user or password.')
#         else:
#             if newquery['word1']=='' or newquery['word2']=='':
#                 resp.body = ('\n Provide one pair of words.\n''\n''    ~ Beagle Inc.\n\n')
#             else:
#                 if newquery["model"]=='default':
#                     resp.body = json.dumps(self.handler_default(unquote(newquery['word1']),unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_300':
#                     resp.body = json.dumps(self.handler_FWCA_300(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_128':
#                     resp.body = json.dumps(self.handler_FWCA_128(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_200':
#                     resp.body = json.dumps(self.handler_FWCA_200(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_plain_128':
#                     resp.body = json.dumps(self.handler_FWCA_plain_128(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_plain_200':
#                     resp.body = json.dumps(self.handler_FWCA_plain_200(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='FWCA_plain_300':
#                     resp.body = json.dumps(self.handler_FWCA_plain_300(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='EUlaw_300':
#                     resp.body = json.dumps(self.handler_EUlaw_300(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='EUlaw_128':
#                     resp.body = json.dumps(self.handler_EUlaw_128(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='EUlaw_200':
#                     resp.body = json.dumps(self.handler_EUlaw_200(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"]=='wiki':
#                     resp.body = json.dumps(self.handler_wiki_300(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 elif newquery["model"] == 'googlenews':
#                     resp.body = json.dumps(self.handler_GoogleNews_300(unquote(newquery['word1']), unquote(newquery['word2'])))
#                 else:
#                     resp.body = ('\n Provide one model.\n''\n''    ~ Beagle Inc.\n\n')
#
# class SentenceScoreService_JMT(object):
#     '''Expose a sense2vec handler as a GET service for falcon.'''
#     def __init__(self):
#         self.handler_default = JMT(100, 1e-5, 0.001, np.load('/home/wei/beagleapi/sense2vec_service_sentence/data/data.npz')['data'].item())
#
#     def on_get(self, req, resp, query=''):
#         query1=query.split("&")
#         newquery={}
#         newquery["sentence1"]=''
#         newquery["model"]='default'
#         newquery["sentence2"] = ''
#         newquery['user'] = ''
#         newquery['password'] = ''
#         for each in query1:
#             try:
#                 if each.split("=")[0]=='sentence1':
#                     newquery["sentence1"] = each.split("=")[1]
#                 if each.split("=")[0] == 'model':
#                    newquery["model"] = each.split("=")[1]
#                 if each.split("=")[0] == 'sentence2':
#                    newquery["sentence2"] = each.split("=")[1]
#                 try:
#                     if each.split("=")[0]=='user':
#                         newquery["user"] = each.split("=")[1]
#                     if each.split("=")[0]=='password':
#                         newquery["password"] = each.split("=")[1]
#                 except:
#                     resp.body = ('\n Provide user and password.')
#             except:
#                 resp.body = ('\n Provide correct query.\n''\n''    ~ Beagle Inc.\n\n')
#         if newquery["user"] != 'Beagle' or newquery["password"] != 'GreatBeagleAI':
#             resp.body = ('\n Provide correct user or password.')
#         else:
#             if newquery['sentence1']=='' or newquery['sentence2']=='':
#                 resp.body = ('\n Provide one pair of sentences.\n''\n''    ~ Beagle Inc.\n\n')
#             else:
#                 if newquery["model"]=='default':
#                     resp.body = json.dumps(self.handler_default(unquote(newquery['sentence1']),unquote(newquery['sentence2'])))
#                 else:
#                     resp.body = ('\n Provide one model.\n''\n''    ~ Beagle Inc.\n\n')
#
# class PartyIdentifierService(object):
#     '''Expose a sense2vec handler as a GET service for falcon.'''
#     def __init__(self):
#         self.handler_default = partyIdentifier(spacy.load('en'))
#
#     def on_post(self, req, resp):
#         txtFile = req.get_param('file')
#         user=req.get_param('user')
#         password = req.get_param('password')
#         #print(txtFile.file.read())
#         if user!='Beagle' or  password!='GreatBeagleAI':
#             resp.body = ('\n Provide correct user or password.')
#         else:
#             resp.body = json.dumps(self.handler_default(txtFile))
#
# class DefintionService(object):
#     '''Expose a sense2vec handler as a GET service for falcon.'''
#     def __init__(self):
#         self.handler_default = definitions()
#
#     def on_post(self, req, resp):
#         txtFile = req.get_param('file')
#         user=req.get_param('user')
#         password = req.get_param('password')
#         #print(txtFile.file.read())
#         if user!='Beagle' or  password!='GreatBeagleAI':
#             resp.body = ('\n Provide correct user or password.')
#         else:
#             resp.body = json.dumps(self.handler_default(txtFile))
#
# class NameEntitiesService(object):
#             '''Expose a sense2vec handler as a GET service for falcon.'''
#
#             def __init__(self):
#                 self.handler_default = nameEntities(spacy.load('en'))
#
#             def on_get(self, req, resp):
#                 sent = req.get_param('sent')
#                 user = req.get_param('user')
#                 password = req.get_param('password')
#                 # print(txtFile.file.read())
#                 if user != 'Beagle' or password != 'GreatBeagleAI':
#                     resp.body = ('\n Provide correct user or password.')
#                 else:
#                     resp.body = json.dumps(self.handler_default(sent))



class SentenceSplittingService(object):
    '''Expose a sentence list'''

    def __init__(self):
        self.handler_default = sentenceTokenizer()
    def on_post(self, req, resp):
        text = json.load(req.bounded_stream)
        text = text['text']
        resp.media = json.dumps(self.handler_default(text))

class SentenceVectorService(object):
    '''Expose a sentence list'''

    def __init__(self):
        self.handler = sentenceVectorizer()
    def on_post(self, req, resp):
        sentences = json.load(req.bounded_stream)
        print("-------")
        print(sentences)
        print(self.handler_default(sentences['sentences']))
        resp.media = json.dumps(self.handler(sentences['sentences']))


# class SentenceGeneration(object):
#     '''Expose a sense2vec handler as a GET service for falcon.'''
#     def __init__(self):
#         self.handler_textGeneration = TextGeneration(spacy.load('en', parser=False, entity=False))
#
#         # self.handler_train = ModelTrain(spacy.load('en', parser=False, entity=False))
#
#     def on_get(self, req, resp, query=''):
#         query1=query.split("&")
#         newquery={}
#         newquery["numberOfSent"]='1'
#         newquery["model"]='default'
#         newquery["startingPhrase"] = ""
#         newquery["mode"] = ""
#         newquery['user']=''
#         newquery['password']=''
#         for each in query1:
#             try:
#                 if each.split("=")[0]=='numberOfSent':
#                     newquery["numberOfSent"] = each.split("=")[1]
#                 if each.split("=")[0] == 'model':
#                    newquery["model"] = each.split("=")[1]
#                 if each.split("=")[0] == 'mode':
#                    newquery["mode"] = each.split("=")[1]
#                 if each.split("=")[0] == 'startingPhrase':
#                    newquery["startingPhrase"] = each.split("=")[1]
#                 try:
#                     if each.split("=")[0]=='user':
#                         newquery["user"] = each.split("=")[1]
#                     if each.split("=")[0]=='password':
#                         newquery["password"] = each.split("=")[1]
#                 except:
#                     resp.body = ('\n Provide user and password.')
#             except:
#                 resp.body = ('\n Provide correct query.\n''\n''    ~ Beagle Inc.\n\n')
#
#         if newquery["user"]!='Beagle' or  newquery["password"]!='GreatBeagleAI':
#             resp.body = ('\n Provide correct user or password.')
#
#         else:
#             if newquery["mode"]!="":
#                 resp.body = json.dumps(self.handler_textGeneration(unquote(newquery['mode']),unquote(newquery['numberOfSent']),unquote(newquery['startingPhrase'])))
#
#             else:
#                 resp.body = ('\n Provide one mode.\n''\n''    ~ Beagle Inc.\n\n')



def load():
    '''Load the sense2vec model, and return a falcon API object that exposes
    the SimilarityService.
    '''
    cors = CORS(allow_all_origins=True, allow_all_methods=True, allow_all_headers=True)
    app = falcon.API(middleware=[cors.middleware,MultipartMiddleware()])

    app.add_route('/most_similar/word={word}&model={model}&number={number}', SimilarityService())
    # app.add_route('/similarity_score/{query}', SimilarityScoreService())
    # app.add_route('/sentence_score/{query}', SentenceScoreService_JMT())
    # app.add_route('/nda_parties', PartyIdentifierService())
    # app.add_route('/definitions', DefintionService())
    # app.add_route('/name_entities', NameEntitiesService())
    app.add_route('/sentence_splitting', SentenceSplittingService())
    app.add_route('/sentence_vector', SentenceVectorService())
    #app.add_route('/sentence_generation/{query}', SentenceGeneration())

    return app



