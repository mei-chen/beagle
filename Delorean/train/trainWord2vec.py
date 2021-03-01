# encoding=utf8


from __future__ import print_function, unicode_literals, division
import io
import bz2
import logging
from os import path
import os
import random
from collections import defaultdict

import plac
try:
    import ujson as json
except ImportError:
    import json
from gensim.models import Word2Vec
from preshed.counter import PreshCounter
from spacy.strings import hash_string

import time
logger = logging.getLogger(__name__)


class Corpus(object):
    def __init__(self, directory, min_freq=10):
        self.directory = directory
        self.counts = PreshCounter()
        self.strings = {}
        self.min_freq = min_freq

    def count_doc(self, words):
        # Get counts for this document
        doc_counts = PreshCounter()
        doc_strings = {}
        for word in words:
            key = hash_string(word)
            doc_counts.inc(key, 1)
            doc_strings[key] = word

        n = 0
        for key, count in doc_counts:
            self.counts.inc(key, count)
            # TODO: Why doesn't inc return this? =/
            corpus_count = self.counts[key]
            # Remember the string when we exceed min count
            if corpus_count >= self.min_freq and (corpus_count - count) < self.min_freq:
                 self.strings[key] = doc_strings[key]
            n += count
        return n

    def __iter__(self):
        for text_loc in iter_dir(self.directory):
            print(text_loc)
            with io.open(text_loc, 'r', encoding='utf8',errors='ignore') as file_:
                sent_strs = list(file_)
                random.shuffle(sent_strs)
                for sent_str in sent_strs:
                    yield sent_str.split()


def iter_dir(loc):
    for fn in os.listdir(loc):
        if path.isdir(path.join(loc, fn)):
            for sub in os.listdir(path.join(loc, fn)):
                yield path.join(loc, fn, sub)
        else:
            yield path.join(loc, fn)

@plac.annotations(
    in_dir=("Location of input directory"),
    out_loc=("Location of output file"),
    n_workers=("Number of workers", "option", "n", int),
    size=("Dimension of the word vectors", "option", "d", int),
    window=("Context window size", "option", "w", int),
    min_count=("Min count", "option", "m", int),
    negative=("Number of negative samples", "option", "g", int),
    nr_iter=("Number of iterations", "option", "i", int),
)


# window=10 for skip and 5 for COW

def main(in_dir, out_loc, negative=5, n_workers=24, window=10, size=300, min_count=10, nr_iter=30,skipGram=1):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    model = Word2Vec(
        size=size,
        window=window,
        min_count=min_count,
        workers=n_workers,
        sample=1e-5,
        sg=skipGram,
        negative=negative
    )
    corpus = Corpus(in_dir)
    total_words = 0
    total_sents = 0
    for text_no, text_loc in enumerate(iter_dir(corpus.directory)):
        print(text_loc)
        try:
            with io.open(text_loc, 'r', encoding='utf8', errors='ignore') as file_:
                text = file_.read()
                #print(text)

        except:
            with io.open(text_loc, 'r', encoding='windows-1252', errors='ignore') as file_:
                text = file_.read()
                #print(text)

        total_sents += text.count('\n')
        print(total_sents)
        total_words += corpus.count_doc(text.split())
        logger.info("PROGRESS: at batch #%i, processed %i words, keeping %i word types",
                    text_no, total_words, len(corpus.strings))
    model.corpus_count = total_sents
    print(model.corpus_count)
    model.raw_vocab = defaultdict(int)
    for key, string in corpus.strings.items():
        model.raw_vocab[string] = corpus.counts[key]
    model.scale_vocab()
    model.finalize_vocab()
    model.iter = nr_iter
    ## the train method is changed!!!!
    #model.train(corpus,total_examples=model.corpus_count, epochs=model.iter)
    model.train(corpus,total_examples=model.corpus_count)

    model.save(out_loc)

if __name__ == '__main__':
    print("start training")
    start_time = time.time()
    plac.call(main)
    print("end training")
    print("--- %s seconds ---" % (time.time() - start_time))

