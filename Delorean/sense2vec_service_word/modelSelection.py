import sense2vec
from sense2vec.vectors import VectorMap
from gensim.models import Word2Vec,KeyedVectors

def load_FWCA_300():
    vector_map = VectorMap(300)
    vector_map.load('/mnt/model_300_FWCA')
    return vector_map

def load_FWCA_200():
    vector_map = VectorMap(200)
    vector_map.load('/mnt/model_200_FWCA')
    return vector_map


def load_FWCA_128():
    vector_map = VectorMap(128)
    vector_map.load('/mnt/model_128_FWCA')
    return vector_map

def load_FWCA_plain_128():
    model = Word2Vec.load('/mnt/corpus/FWCA_model_128/FWCA_128_plain.word2vec')
    return model

def load_FWCA_plain_200():
    model = Word2Vec.load('/mnt/corpus/FWCA_model_200/FWCA_200_plain.word2vec')
    return model

def load_FWCA_plain_300():
    model = Word2Vec.load('/mnt/corpus/FWCA_model_300/FWCA_300_plain.word2vec')
    return model

def load_wiki_300():
    model = Word2Vec.load('/mnt/corpus/wiki_model_300/wiki_model_300.word2vec')
    return model

def load_GoogleNews_300():
    model = KeyedVectors.load_word2vec_format('/mnt/corpus/GoogleNews_model_300/GoogleNews-vectors-negative300.bin', binary=True)
    return model


def load_EUlaw_300():
    vector_map = VectorMap(300)
    vector_map.load('/mnt/model_EUlaw_300')
    return vector_map

def load_EUlaw_128():
    vector_map = VectorMap(128)
    vector_map.load('/mnt/model_EUlaw_128')
    return vector_map

def load_EUlaw_200():
    vector_map = VectorMap(200)
    vector_map.load('/mnt/model_EUlaw_200')
    return vector_map