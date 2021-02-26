from nlplib.generics import GenericAnalyzer
from nlplib.grammars import TERMINATION_GRAMMAR, TERMINATION_TYPES


class TerminationAnalyzer(GenericAnalyzer):
    def __init__(self, wordtagged, mention_clusters, them_party, you_party):
        super(TerminationAnalyzer, self).__init__(wordtagged, mention_clusters, them_party, you_party)

    @property
    def _analyzer_grammar(self):
        return TERMINATION_GRAMMAR

    @property
    def _result_types(self):
        return TERMINATION_TYPES

    @property
    def terminations(self):
        return self.results

    def readable_terminations(self, mention):
        return self.readable_results(mention)