How to Train a Word2Vec Library

Please note the approach we take is little bit different from the standard training approach. Before trainging the library for a given corpus, we will cleanup by removing line breakers et al, followed by NLP processing by adding POS, recognizing name entities and noun phrases, et. al.

Suppose we are given a corpus with a lot of unstructured, noise plain text files.

1. Run  python cleanText.py in_dir out_dir, where in_dir is the folder name containing all corpus files, and out_dir is the output folder name containing all cleaned up files with extension .clean.

2. Run python taggingText.py cleaned_dir  tagged_dir n_CPUs,  where cleaned_dir is the cleaned folder name containing all cleaned up files,tagged_dir is the folder saving files with tagged tokens, and n_CPUs is the number of cpus for paralleling tagging. Make sure tagged_dir is empty. Note this step will takes days for large corpus.

3. Run python trainWord2vec.py in_dir out_model_name negative n_cpus window size min_count nr_iter skipGram, where in_dir is the folder of tagged corpus, out_model_name is the trained model model name, all of other have default values negative=5, n_cpus=24, window=10, size=300, min_count=10, nr_iter=30, skipGram=1. This traing is the same as the standard Gensim Word2Vec traing method.