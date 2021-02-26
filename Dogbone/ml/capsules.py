"""
Wrappers for information to be passed around. Should contain all the info
needed by classifiers and other ml module components.
"""

from ml.utils import party_pattern
from nlplib.utils import preformat_markers


class Capsule:
    """ Encapsulates main sentence info needed for ml module components. """

    def __init__(self, text, idx=-1, flags=[], parties={}):
        # Sentence text
        self.text = text
        # Sentence index (i.e. sequence number in its containing document)
        self.idx = idx
        # List of flags
        self.flags = flags
        # Dict of document parties
        self.parties = parties

    def preprocess(self, you_party=None, them_party=None):
        """
        Strip the party names from the text to achieve better generalization.
        If no re-s are provided (patterns for the parties) and the parties
        dict is available, then appropriate party re-s are inferred.
        :param you_party: re object
        :param them_party: re object
        """
        text = self.text

        if self.parties:
            if you_party is None:
                yparty = self.parties.get('you')
                if yparty:
                    you_party = party_pattern(yparty)

            if them_party is None:
                tparty = self.parties.get('them')
                if tparty:
                    them_party = party_pattern(tparty)

        if you_party:
            text = you_party.sub('__YOU_PARTY__', text)

        if them_party:
            text = them_party.sub('__THEM_PARTY__', text)

        return preformat_markers(text)
