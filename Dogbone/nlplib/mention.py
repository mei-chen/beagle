from nltk import RegexpParser
from nlplib.grammars import MENTIONS_GRAMMAR

mention_parser = RegexpParser(MENTIONS_GRAMMAR, trace=0)


def parse_mentions(wt_text):
    """ Apply the mention grammar on a wordtagged sentence """
    return mention_parser.parse(wt_text)

