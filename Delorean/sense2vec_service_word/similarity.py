from __future__ import unicode_literals
import logging
from gensim.models import Word2Vec,KeyedVectors

# class Similarity(object):
#     '''
#     Handle sense2vec similarity queries.
#     '''
#     def __init__(self, spacy_nlp, sense2vec_vector_map):
#         self.nlp = spacy_nlp
#         self.w2v = sense2vec_vector_map
#         self.lemmatizer = self.nlp.vocab.morphology.lemmatizer
#         self.parts_of_speech = ['NOUN', 'VERB', 'ADJ', 'ORG', 'PERSON', 'FAC',
#                                 'PRODUCT', 'LOC', 'GPE']
#         logging.info("Serve")
#
#     def __call__(self, query, n=10):
#         # Don't return the original
#         logging.info("Find best query")
#         key = self._find_best_key(query)
#         logging.info("Key=", repr(key))
#
#         if not query or not key:
#             return {'key': '', 'text': query, 'results': [], 'count': 0}
#         text = key.rsplit('|', 1)[0].replace('_', ' ')
#         results = []
#         seen = set([text])
#
#         seen.add(self._find_head(key))
#         for entry, score in self.get_similar(key, n * 2):
#
#             head = self._find_head(entry)
#             freq, _ = self.w2v[entry]
#             if head not in seen:
#                 results.append(
#                     {
#                         'score': score,
#                          'key': entry,
#                          'text': entry.split('|')[0].replace('_', ' '),
#                          'count': freq,
#                          'head': head
#                     })
#                 seen.add(head)
#             if len(results) >= n:
#                 break
#         freq, _ = self.w2v[key]
#
#         return {'text': text, 'key': key, 'results': results,
#                 'count': freq,
#                 'head': self._find_head(key)}
#
#     def _find_best_key(self, query):
#         query = query.replace(' ', '_')
#         if '|' in query:
#             text, pos = query.rsplit('|', 1)
#             key = text + '|' + pos.upper()
#             return key if key in self.w2v else None
#
#         freqs = []
#         casings = [query, query.upper(), query.title()] if query.islower() else [query]
#         for text in casings:
#             for pos in self.parts_of_speech:
#                 key = text + '|' + pos
#                 if key in self.w2v:
#                     freqs.append((self.w2v[key][0], key))
#         return max(freqs)[1] if freqs else None
#
#     def _find_head(self, entry):
#         if '|' not in entry:
#             return entry.lower()
#         text, pos = entry.rsplit('|', 1)
#         head = text.split('_')[-1]
#         return min(self.lemmatizer(head, pos))
#
#
#     def get_similar(self, query, n):
#         print(query)
#         if query not in self.w2v:
#             print('not in word set')
#             return []
#         freq, query_vector = self.w2v[query]
#         # print(freq)
#         # print(query_vector)
#         words, scores = self.w2v.most_similar(query_vector, n)
#         # print(words)
#         # print(scores)
#         return zip(words, scores)


# class Similarity_wiki_300(object):
#     '''
#     Handle sense2vec similarity queries.
#     '''
#     def __init__(self,word2vec):
#         self.w2v = word2vec
#
#     def __call__(self, query, n=10):
#         results=[]
#         for entry, score in self.get_similar(query, n * 2):
#                 results.append(
#                     {
#                         'score': score,
#                          'key': entry,
#                          'text': entry.split('|')[0].replace('_', ' '),
#                          'count': '',
#                          'head': entry
#                     })
#                 if len(results) >= n:
#                     break
#
#         return {'text': query, 'key': query, 'results': results,
#                 'count': '',
#                 'head': query}
#
#     def get_similar(self, query, n):
#         print(query)
#         if query not in self.w2v:
#             print('not in word set')
#             return []
#         words=[]
#         scores=[]
#         for each in self.w2v.most_similar(query, topn=n):
#             #print list(each)
#             words.append(list(each)[0])
#             scores.append(list(each)[1])
#         # print(words)
#         # print(scores)
#         return zip(words, scores)


class Similarity_GoogleNews(object):
    '''
    Handle sense2vec similarity queries.
    '''
    def __init__(self,model):
        self.w2v = model
    def __call__(self, query, n=10):
        results=[]
        for entry, score in self.get_similar(query, n):
                results.append(
                    {
                        'score': score,
                         'key': entry,
                         'text': entry.split('|')[0].replace('_', ' '),
                         'head': entry
                    })
                if len(results) >= n:
                    break

        return {'text': query, 'key': query, 'results': results,
                'head': query}

    def get_similar(self, query, n):
        if query not in self.w2v:
            print('not in word set')
            return []
        words=[]
        scores=[]
        for each in self.w2v.most_similar(query, topn=n):
            words.append(list(each)[0])
            scores.append(list(each)[1])
        return zip(words, scores)


class Similarity(object):
    '''
    Handle sense2vec similarity queries.
    '''
    def __init__(self, spacy_nlp,model):
        self.nlp = spacy_nlp
        self.w2v = model
        # self.lemmatizer = self.nlp.vocab.morphology.lemmatizer
        self.parts_of_speech = ['NOUN', 'VERB', 'ADJ', 'ORG', 'PERSON', 'FAC',
                                'PRODUCT', 'LOC', 'GPE']
        logging.info("Serve")

    def __call__(self, query, n=10):
        # Don't return the original
        logging.info("Find best query")
        key = self._find_best_key(query)
        logging.info("Key=", repr(key))

        if not query or not key:
            return {'key': '', 'text': query, 'results': [], 'count': 0}
        text = key.rsplit('|', 1)[0].replace('_', ' ')
        results = []
        seen = set([text])

        seen.add(self._find_head(key))
        for entry, score in self.get_similar(key, n * 2):
            head = self._find_head(entry)
            if head not in seen:
                results.append(
                    {
                        'score': score,
                         'key': entry,
                         'text': entry.split('|')[0].replace('_', ' '),
                         'head': head
                    })
                seen.add(head)
            if len(results) >= n:
                break

        return {'text': text, 'key': key, 'results': results,
                'head': self._find_head(key)}

    def _find_best_key(self, query):
        query = query.replace(' ', '_')
        if '|' in query:
            text, pos = query.rsplit('|', 1)
            key = text + '|' + pos.upper()
            return key if key in self.w2v.wv else None

        freqs = []
        casings = [query, query.upper(), query.title()] if query.islower() else [query]
        for text in casings:
            for pos in self.parts_of_speech:
                key = text + '|' + pos
                if key in self.w2v.wv:
                    freqs.append((self.w2v.wv[key][0], key))
        return max(freqs)[1] if freqs else None

    def _find_head(self, entry):
        if '|' not in entry:
            return entry.lower()
        text, pos = entry.rsplit('|', 1)
        head = text.split('_')[-1]
        # return min(self.lemmatizer(head, pos))
        return min(head, pos)

    def get_similar(self, query, n):
        if query not in self.w2v.wv:
            print('not in word set')
            return []
        # freq, query_vector = self.w2v[query]
        # print(freq)
        # print(query_vector)
        return self.w2v.wv.most_similar(query)

