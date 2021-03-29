from nlplib.coreference import CoreferenceResolution
from nlplib.partycounter import PartyCounterExtractor
from nlplib.mention import parse_mentions
from nlplib.references import ExternalReferencesAnalyzer
from nlplib.liability import LiabilityAnalyzer
from nlplib.responsibility import ResponsibilityAnalyzer
from nlplib.termination import TerminationAnalyzer
from nlplib.utils import (
    preprocess_text, postprocess_text, split_sentences,
    remove_linebreak_markers, sents2wordtag,
)


class NlplibFacade:
    def __init__(self, text=None, sentences=None, parties=None):
        '''
        Lazy initializes the facade.

        If provided, @parties must have the format:
            (them_party, you_party, (confidence_them, confidence_you))

        Mostly for backwards compatibility, a facade can be initialized by
        either raw text or by a list of sentences.
        '''
        self._rawsentences = sentences
        self._text = text
        self._wordtagged = None
        self._preprocessed_sentences = None
        self._processed_text = None
        self._mention_clusters = None
        self._parsed_mentions = None
        self._clusters = None
        self._parties = None
        if parties:
            self._parties = parties
        self._external_references = None
        self._coreference_resolution = None
        self._party_counter = None
        self._external_references_analyzer = None
        self._liabilities_analyzer = None
        self._responsibilities_analyzer = None
        self._termination_analyzer = None

    @property
    def coreference_resolution(self):
        if self._coreference_resolution is None:
            them_party = None
            you_party = None
            if self._parties:
                them_party, you_party, _ = self._parties
            self._coreference_resolution = CoreferenceResolution(self.parsed_mentions,
                                                                 parties=(them_party, you_party))

        return self._coreference_resolution

    @property
    def party_counter(self):
        if self._party_counter is None:
            clean_txt = remove_linebreak_markers(self.text)
            clean_sents = list(map(remove_linebreak_markers, self.sentences))
            self._party_counter = PartyCounterExtractor(clean_txt, clean_sents)

        return self._party_counter

    @property
    def external_references_analyzer(self):
        if self._external_references_analyzer is None:
            self._external_references_analyzer = ExternalReferencesAnalyzer(
                                                    self.text, self.sentences,
                                                    self.wordtagged,
                                                    self.parties[:2])

        return self._external_references_analyzer

    @property
    def liabilities_analyzer(self):
        if self._liabilities_analyzer is None:
            them_party, you_party, _ = self.parties
            self._liabilities_analyzer = LiabilityAnalyzer(
                self.wordtagged,
                self.clusters,
                them_party,
                you_party,
            )

        return self._liabilities_analyzer

    @property
    def responsibilities_analyzer(self):
        if self._responsibilities_analyzer is None:
            them_party, you_party, _ = self.parties
            self._responsibilities_analyzer = ResponsibilityAnalyzer(
                self.wordtagged,
                self.clusters,
                them_party,
                you_party,
            )

        return self._responsibilities_analyzer

    @property
    def termination_analyzer(self):
        if self._termination_analyzer is None:
            them_party, you_party, _ = self.parties
            self._termination_analyzer = TerminationAnalyzer(
                self.wordtagged,
                self.clusters,
                them_party,
                you_party,
            )

        return self._termination_analyzer


    @property
    def text(self):
        if self._text is None and not self._rawsentences is None:
            self._text = ' '.join(self._rawsentences)
        return self._text

    @property
    def sentences(self):
        if self._rawsentences is None and not self.text is None:
            self._rawsentences = split_sentences(self.text)
        return self._rawsentences


    @property
    def processed_text(self):
        if self._processed_text is None:
            self._processed_text = list(map(postprocess_text, self.preprocessed_sentences))
        return self._processed_text

    @property
    def preprocessed_sentences(self):
        if self._preprocessed_sentences is None:
            self._preprocessed_sentences = list(map(preprocess_text, self.sentences))

        return self._preprocessed_sentences

    @property
    def wordtagged(self):
        if self._wordtagged is None:
            self._wordtagged = sents2wordtag(self.preprocessed_sentences)

        return self._wordtagged

    @property
    def parsed_mentions(self):
        if self._parsed_mentions is None:
            self._parsed_mentions = [parse_mentions(ss) for ss in self.wordtagged]

        return self._parsed_mentions

    @property
    def clusters(self):
        ''' Clusters of parties/mentions '''
        if self._clusters is None:
            coref = self.coreference_resolution
            self._clusters = coref.resolute()

        return self._clusters

    @property
    def parties(self):
        if self._parties is None:
            extractor = self.party_counter
            # Disable coref clusters until they get useful
            # self._parties = extractor.extract_parties(self.clusters)
            self._parties = extractor.extract_parties()
        return self._parties

    @property
    def formated_clusters(self):
        ''' Formatted output for clusters of parties/mentions '''
        clusters = []
        for p in self.clusters:
            clusters.append((p.most_relevant(), list(p.forms()) + list(p.possible_forms())))

        return clusters

    def party_by_mention(self, m):
        for p in self.clusters:
            if m in p.forms():
                return m
        return None

    @property
    def external_references(self):
        if self._external_references is None:
            analyzer = self.external_references_analyzer
            analyzer.analyze()
            self._external_references = analyzer.references
        return self._external_references

    def liabilities(self, mention):
        return self.liabilities_analyzer.readable_results(mention)

    def responsibilities(self, mention):
        return self.responsibilities_analyzer.readable_results(mention)

    def terminations(self, mention):
        return self.termination_analyzer.readable_results(mention)

    def run_all_analyzers(self, mention=None):
        from itertools import chain

        def run_analyzer(task):
            name, analyzer, mention = task
            return name, analyzer.readable_results(mention), mention

        if mention is None:
            them_party, you_party, _ = self.parties
            tasks = list(chain(*[
                [
                    ('liabilities', self.liabilities_analyzer, mention),
                    ('responsibilities', self.responsibilities_analyzer, mention),
                    ('terminations', self.termination_analyzer, mention),
                ]
                for mention in ['both', them_party, you_party]
            ]))
        else:
            tasks = [
                ('liabilities', self.liabilities_analyzer, mention),
                ('responsibilities', self.responsibilities_analyzer, mention),
                ('terminations', self.termination_analyzer, mention),
            ]
        results = [run_analyzer(x) for x in tasks]
        return results
