
from gensim.models import Word2Vec,KeyedVectors

def load_models():
    google_news = KeyedVectors.load_word2vec_format('models/google_news/GoogleNews-vectors-negative300.bin', binary=True)
    eu_law = Word2Vec.load('models/model_EULaw/EULaw.word2vec')
    us_law = Word2Vec.load('models/US_contracts/lawinsider.word2vec')
    return google_news,eu_law,us_law
