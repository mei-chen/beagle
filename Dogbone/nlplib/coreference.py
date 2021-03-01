from nlplib.utils import extract_nodes, tree2str, IdGenerator
from nlplib.utils import get_unicode, hPers
from nlplib.utils import fuzzy_pronoun_match, prepare_company_name, remove_determiners, basic_forms, STANDARD_ENTITY_NOTATIONS
from nlplib.tokenizing.splitta.splitta import splitta_word_tokenize as word_tokenize
import re


escape_re = re.compile(r'([.?()-])')
unescapable_re = re.compile(r'([<>]+)')

def mention2regex(form):
    regex = ""
    # The +' ' is a hack to force word_tokenize to not split the . from e.g. Inc.
    tokens = word_tokenize(form + ' ')[:-1]
    for tok in tokens:
        esctok = escape_re.sub(r'\\\1', tok)
        esctok = unescapable_re.sub('', esctok)
        btok = basic_forms(esctok)
        if btok:
            if esctok not in btok:
                btok.append(esctok)
            regex += "<("+ '|'.join(btok) +")__.*>"

    return regex


class MentionCluster:
    def __init__(self, mentions=None):
        if mentions is None:
            mentions = []

        self.mentions = mentions

    def merge(self, cluster):
        self.mentions.extend(cluster.mentions)

    def filter(self, predicate):
        return [m for m in self.mentions if predicate(m)]

    def most_relevant(self):
        companies = self.filter(lambda x: x['type'] == 'COMPANY_MENTION')

        if companies:
            companies = sorted(companies, key=lambda x: len(x['form']), reverse=True)
            return companies[0]['form']

        pronouns = self.filter(lambda x: x['type'] == 'PRONOUN_MENTION')

        if pronouns:
            return pronouns[0]['form']
        try:
            return self.mentions[0]['form']
        except IndexError:
            return None

    def add_form(self, form):
        self.mentions.append({'form': form, 'type': 'ENTITY_MENTION'})

    def forms(self):
        return set([m['form'].strip() for m in self.mentions])

    def possible_forms(self):
        p_forms = []

        for m in self.filter(lambda x: x['type'] in ('ENTITY_MENTION', 'COMPANY_MENTION')):
            p_forms.extend(MentionCluster.abbreviate(m['form']))

            if '"' in m['form']:
                f = m['form'].replace('"', '')
                f = f.replace('  ', ' ')
                f = f.strip()
                p_forms.append(f)
                ff = f.strip(', ')
                if ff != f:
                    p_forms.append(ff)

            # Remove standard notations
            if prepare_company_name(m['form']) != m['form']:
                p_forms.append(prepare_company_name(m['form']))

            # Remove determiners
            if remove_determiners(m['form']) != m['form']:
                frm = remove_determiners(m['form'])
                if frm:
                    p_forms.extend(basic_forms(frm))

        return set(p_forms)

    def all_forms(self):
        return self.forms().union(self.possible_forms())


    @staticmethod
    def abbreviate(form):
        form = MentionCluster.remove_common_abbrev(form)
        chunks = form.split(' ')
        if len(chunks) <= 2:
            return []
        return [d.join([c[0].upper() for c in chunks]) for d in ('', '.', '-')] + \
               [d.join([c[0].upper() for c in chunks]) + d for d in ('.',)]

    @staticmethod
    def normalize(form):
        form = form.lower()
        chars = " _-.,/\\&%'\""
        for c in chars:
            form = form.replace(c, '')
        return get_unicode(form)

    @staticmethod
    def remove_common_abbrev(form):
        form = form.lower()
        chars = " _-.,/\\&%'\""
        for c in chars:
            form = form.replace(c, ' ')

        form = ' ' + form + ' '
        for abbrev in STANDARD_ENTITY_NOTATIONS:
            form = form.replace(' ' + abbrev + ' ', ' ')

        return re.sub(' +', ' ', form).strip()

    def fuzzy_match(self, word):
        nrm_word = get_unicode(word.strip())
        for m in self.mentions:
            nrm_ment = get_unicode(m['form'].strip())
            if nrm_word.lower() == nrm_ment.lower() or nrm_ment.startswith(nrm_word + ' '):
                return True

    def __contains__(self, form):
        for m in self.mentions:
            if isinstance(form, basestring) \
                    and MentionCluster.normalize(m['form']) == MentionCluster.normalize(form):
                return True
            elif isinstance(form, dict) \
                    and MentionCluster.normalize(m['form']) == MentionCluster.normalize(form['form']):
                return True
        return False

    def __iter__(self):
        return iter(self.mentions)

    def __len__(self):
        return len(self.mentions)

    def __str__(self):
        return '{%s :: %s %s}' % (
                str(self.most_relevant()),
                '|'.join(self.forms()),
                '// ' + '|'.join(self.possible_forms()) if self.possible_forms() else ''
            )

    def __repr__(self):
        return self.__str__()


class CoreferenceResolution:
    def __init__(self, parsed_sentences, parties=None):
        self.parsed_sentences = parsed_sentences
        self._indicators = None
        self.clusters = None
        self.parties = parties

    @property
    def indicators(self):
        if not self._indicators:
            indicators = []
            for ps in self.parsed_sentences:
                indicators.extend([n[0] for n in extract_nodes(ps, label='MENTION_INDICATOR')])

            self._indicators = indicators

        return self._indicators

    def _cluster_mention(self, m):
        return [{'form': tree2str(m[0]), 'type': m[0].label(), 'id': IdGenerator.get('mention')}]

    def _cluster_apposition(self, mn):
        mentions = extract_nodes(mn, label='MENTION')
        return [{'form': tree2str(m[0]), 'type': m[0].label(), 'id': IdGenerator.get('mention')}
                for m in mentions]

    def _string_match_sieve(self):
        new_clusters = [self.clusters[0]]

        for cluster in self.clusters[1:]:
            merged = False
            for new_cluster in new_clusters[:]:
                for m in cluster.all_forms():
                    if m in new_cluster:
                        new_cluster.merge(cluster)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                new_clusters.append(cluster)

        self.clusters = new_clusters

    def _pronoun_match_sieve(self):
        new_clusters = [self.clusters[0]]

        for cluster in self.clusters[1:]:
            merged = False
            for new_cluster in new_clusters[:]:
                for m in cluster.filter(lambda x: x['type'] == 'PRONOUN_MENTION'):
                    if new_cluster.filter(lambda x: x['type'] == 'PRONOUN_MENTION'
                                          and fuzzy_pronoun_match(x['form'], m['form'])):
                        new_cluster.merge(cluster)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                new_clusters.append(cluster)

        self.clusters = new_clusters

    def _entity_company_match_sieve(self):
        new_clusters = [self.clusters[0]]

        for cluster in self.clusters[1:]:
            merged = False
            for new_cluster in new_clusters[:]:
                for m in cluster.filter(lambda x: x['type'] in ['COMPANY_MENTION', 'ENTITY_MENTION']):
                    if new_cluster.filter(lambda x: x['type'] in ['COMPANY_MENTION', 'ENTITY_MENTION']
                                          and MentionCluster.remove_common_abbrev(x['form']) ==
                                          MentionCluster.remove_common_abbrev(m['form'])):
                        new_cluster.merge(cluster)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                new_clusters.append(cluster)

        self.clusters = new_clusters

    def _business_rules_match_sieve(self):
        new_clusters = [self.clusters[0]]

        rules = [
            ('you', 'licensee'),
            ('you', 'user'),
            ('you', 'end-user'),
            ('you', 'customer'),
            ('user', 'customer'),
            ('we', 'licensor'),
        ]

        for cluster in self.clusters[1:]:
            merged = False
            for new_cluster in new_clusters[:]:
                for rule in rules:
                    if rule[0] in cluster and rule[1] in new_cluster:
                        new_cluster.merge(cluster)
                        merged = True
                        break
                    if rule[1] in cluster and rule[0] in new_cluster:
                        new_cluster.merge(cluster)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                new_clusters.append(cluster)

        self.clusters = new_clusters


    def _init_clusters(self):
        self.clusters = []
        # Init clusters with the parties if given
        if self.parties:
            self.clusters.append(MentionCluster([{'form': self.parties[0],
                                                  'type': 'ENTITY_MENTION',
                                                  'id': IdGenerator.get('mention')}]))
            self.clusters.append(MentionCluster([{'form': self.parties[1],
                                                  'type': 'ENTITY_MENTION',
                                                  'id': IdGenerator.get('mention')}]))

            # TODO: figure out whether the statement below is really needed,
            # because right now it causes "asymmetry", i.e. changing the
            # order of the parties may produce different results

            # If one party is refered by using a pronoun, assume the other will too
            # if any(map(lambda x: x.lower() in hPers, self.parties)):
            #     self.clusters[0].add_form('we')
            #     self.clusters[1].add_form('you')

        for indicator in self.indicators:
            if indicator.label() == 'MENTION_LINK':
                mention_groups = extract_nodes(indicator,
                                               predicate=lambda n: n.label() in ['MENTION_APPOSITION', 'MENTION'])

                for m in mention_groups:
                    if m.label() == 'MENTION':
                        self.clusters.append(MentionCluster(self._cluster_mention(m)))
                    elif m.label() == 'MENTION_APPOSITION':
                        self.clusters.append(MentionCluster(self._cluster_apposition(m)))

            elif indicator.label() == 'MENTION_APPOSITION':
                self.clusters.append(MentionCluster(self._cluster_apposition(indicator)))
            elif indicator.label() == 'MENTION':
                self.clusters.append(MentionCluster(self._cluster_mention(indicator)))

    def resolute(self):
        self._init_clusters()
        if not self.clusters: # No cluster found
            return self.clusters
        self._string_match_sieve()
        self._pronoun_match_sieve()
        self._entity_company_match_sieve()
        self._business_rules_match_sieve()
        self.clusters = sorted(self.clusters, key=len, reverse=True)
        return self.clusters
