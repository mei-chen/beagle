from nltk import RegexpParser

from django.template import Template, Context

from nlplib.coreference import mention2regex
from nlplib.coreference import MentionCluster
from nlplib.utils import extract_nodes

from .data import lazydict


class GenericAnalyzer(object):
    def __init__(self, wordtagged, mention_clusters, them_party, you_party):
        super(GenericAnalyzer, self).__init__()
        self._wordtagged = wordtagged
        self._mention_clusters = mention_clusters
        self._results = None
        self.them_party = them_party
        self.you_party = you_party

    # -- To be implemented in Analyzers --
    @property
    def _analyzer_grammar(self):
        raise NotImplementedError
    @property
    def _result_types(self):
        raise NotImplementedError
    # -- -- --

    @property
    def wordtagged(self):
        return self._wordtagged

    @property
    def mention_clusters(self):
        return self._mention_clusters

    def render_grammar(self, mention_cluster, both=False):
        pm = [mention2regex(m) for m in mention_cluster.all_forms()]
        t = Template(self._analyzer_grammar)
        c = Context({'party_mentions': pm, 'both': both})
        return t.render(c)

    def _extract(self, mention_cluster):
        grammar = self.render_grammar(mention_cluster)
        parser = RegexpParser(grammar)
        parsed_sents = []

        # with open('term.out', 'w') as fout:
        #     fout.write(grammar)

        for wt_sent in self.wordtagged:
            parsed_sents.append(parser.parse(wt_sent))

        return parsed_sents

    def _extract_both(self):
        all_parties_cluster = MentionCluster([])
        found_you, found_them = False, False
        for c in self.mention_clusters:
            if self.them_party in c.forms():
                all_parties_cluster.merge(c)
                found_them = True
            if self.you_party in c.forms():
                all_parties_cluster.merge(c)
                found_you = True

        if not found_them:
            all_parties_cluster.merge(MentionCluster([{'form': self.them_party, 'type': 'ENTITY_MENTION'}]))
        if not found_you:
            all_parties_cluster.merge(MentionCluster([{'form': self.you_party, 'type': 'ENTITY_MENTION'}]))

        grammar = self.render_grammar(all_parties_cluster, both=True)
        parser = RegexpParser(grammar)
        parsed_sents = []

        for wt_sent in self.wordtagged:
            parsed_sents.append(parser.parse(wt_sent))

        return parsed_sents

    def _process(self, mention_cluster):
        parsed = self._extract(mention_cluster)
        l_results = []

        for idx, p_sent in enumerate(parsed):
            found_nodes = extract_nodes(p_sent, predicate=lambda node: node.label() in self._result_types)
            if found_nodes:
                for fn in found_nodes:
                    annotated_sent = p_sent.copy(deep=True)
                    annotated_sent.set_label(fn.label())
                    # little hack
                    annotated_sent.text_index = idx
                    l_results.append(annotated_sent)

        return l_results

    def _process_both(self):
        parsed = self._extract_both()
        l_results = []

        for idx, p_sent in enumerate(parsed):
            found_nodes = extract_nodes(p_sent, predicate=lambda node: node.label() in self._result_types)
            if found_nodes:
                for fn in found_nodes:
                    annotated_sent = p_sent.copy(deep=True)
                    annotated_sent.set_label(fn.label())
                    # little hack
                    annotated_sent.text_index = idx
                    l_results.append(annotated_sent)

        return l_results

    @property
    def results(self):
        if self._results is None:

            def results_generator(key):
                if key == 'both':
                    return self._process_both()

                for m_cluster in self.mention_clusters:
                    if key in m_cluster:
                        return self._process(m_cluster)

                m_cluster = MentionCluster()
                m_cluster.add_form(key)
                return self._process(m_cluster)

            self._results = lazydict(generator=results_generator)

        return self._results

    def readable_results(self, mention):
        l_results = self.results[mention]
        if l_results is None:
            return {}
        return {t.text_index: t.label() for t in l_results}
