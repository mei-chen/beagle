from nlplib.generics import GenericAnalyzer
from nlplib.grammars import RESPONSIBILITY_GRAMMAR, RESPONSIBILITY_TYPES


class ResponsibilityAnalyzer(GenericAnalyzer):
    def __init__(self, wordtagged, mention_clusters, them_party, you_party):
        super(ResponsibilityAnalyzer, self).__init__(wordtagged, mention_clusters, them_party, you_party)

    @property
    def _analyzer_grammar(self):
        return RESPONSIBILITY_GRAMMAR

    @property
    def _result_types(self):
        return RESPONSIBILITY_TYPES

    @property
    def responsibilities(self):
        return self.results

    def readable_responsibilities(self, mention):
        return self.readable_results(mention)
