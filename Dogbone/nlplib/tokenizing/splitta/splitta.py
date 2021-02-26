from word_tokenize import tokenize
from sbd import get_text_data, load_sbd_model
import os

MODEL_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'model_nb')
MODEL = load_sbd_model(MODEL_PATH)


def splitta_word_tokenize(text):

    def tweak_last_word(sent):
        """
        As Splitta doesn't separate the last . of the sentence, this
        function does it.
        """
        if sent and sent[-1].endswith('.'):
            last_word = sent.pop().rstrip('.')
            if last_word:
                sent.append(last_word)
            sent.append('.')
        return sent

    sent = tokenize(text).split(' ')
    sent = tweak_last_word(sent)
    return sent


def splitta_sent_tokenize(text):
    model = MODEL
    doc = get_text_data(text, tokenize=False)
    doc.featurize(model, verbose=False)
    model.classify(doc, verbose=False)
    return doc.segment(use_preds=True, output=None)


if __name__ == "__main__":
    print splitta_word_tokenize("And if bankruptcy doesn't do them in, many farmers will likely quit because the financial stress is simply too much, he said. This is the second year in a row that Delmarva farmers are experiencing a less-than-stellar growing season.")

    sentences = splitta_sent_tokenize("``You're going to lose farmers to bankruptcy; there's no way else to say it,'' says Turp Garrett, the agricultural extension agent for Worcester County, Md. ``It's not very pretty.''")
    print sentences
    for sent in sentences:
        print splitta_word_tokenize(sent)

    sentences = splitta_sent_tokenize("John F. Kennedy Jr. , 38 ; his wife , Bessette Kennedy , 33 ; and her sister , Lauren Bessette , 35 , have been missing since Friday evening when Kennedy 's plane left Fairfield , N.J. , for Cape Cod , Mass. , for a Kennedy cousin 's wedding.")
    print sentences
