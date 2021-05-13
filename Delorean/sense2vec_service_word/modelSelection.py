import os
from gensim.models import Word2Vec, KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec


def load_models():
    glove_file_path = './glove.50d.txt'
    word2vec_file_path= './glove.6B.50d.word2vec'
    if not os.path.exists(word2vec_file_path) or os.stat(glove_file_path).st_mtime > os.stat(word2vec_file_path).st_mtime:
        glove2word2vec(glove_file_path, word2vec_file_path)
    word_model = KeyedVectors.load_word2vec_format('./glove.6B.50d.word2vec')
    return word_model, word_model, word_model

#def load_models():
#    google_news = KeyedVectors.load_word2vec_format('models/google_news/GoogleNews-vectors-negative300.bin', binary=True)
#    eu_law = Word2Vec.load('models/model_EULaw/EULaw.word2vec')
#    us_law = Word2Vec.load('models/US_contracts/lawinsider.word2vec')
#    return google_news, eu_law, us_law