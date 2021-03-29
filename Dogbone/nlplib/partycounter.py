import re
import codecs
from collections import Counter
from operator import itemgetter

# import nltk
from nlplib.tokenizing.splitta.splitta import splitta_word_tokenize as word_tokenize
from nlplib.tokenizing.splitta.splitta import splitta_sent_tokenize as sent_tokenize
from nlplib.utils import lemmatize_unify_pronouns
from nlplib.utils import nonPR_stopwords, legal_specific_words, halfed_words
from nlplib.utils import quoted_re, unicode_quote_re, betw_and_re, by_re
from nlplib.utils import liability_re, between_re, rightreserve_re, provide_re
from nlplib.utils import ne_expand_re_fn, party_bad_chars_re, fillin_underscore_re
from nlplib.utils import get_unicode


class PartyCounterExtractor:
    def __init__(self, rawtext, rawsentences=None):
        # Unify all types of double quotes
        unifyquotes = lambda s: unicode_quote_re.sub('"', s)
        rmfillin = lambda s: fillin_underscore_re.sub('', s)
        rawtext = unifyquotes(rawtext)
        rawtext = rmfillin(rawtext)
        # Tokenization and inits
        self.rawtext = rawtext
        if rawsentences is None:
            self.rawsentences = sent_tokenize(rawtext)
        else:
            self.rawsentences = list(map(unifyquotes, rawsentences))
            self.rawsentences = list(map(rmfillin, rawsentences))
        self.stopwords = nonPR_stopwords + legal_specific_words
        # self.lemmzr = nltk.WordNetLemmatizer()

    def extract_parties(self, corefs=None):
        '''
        Extracts the parties involved in a contract
        Returns (them_party, you_party, (them_confidence, you_confidence))
        '''
        pair_list_unpack = lambda tpllst: [c[0] for c in tpllst] + \
                                          [c[1] for c in tpllst]

        truncate = lambda s, length: s[:length] + '...' if len(s) > length else s

        def detected_sent_wcount(sentences, detected_re):
            '''Returns Counter of words in matching sentences'''
            detected_sentences = [s for s in sentences
                                    if detected_re.search(s)]
            detected_toks = [word_tokenize(s) for s in detected_sentences]
            detected_clnt = [t.strip('()*,."\';:-/\\[]{}').encode('utf8', 'replace').strip(codecs.BOM_UTF8)
                             for st in detected_toks for t in st]
            detected_clnt = [lemmatize_unify_pronouns(t.lower()) for t in detected_clnt
                             if t]
            detected_clnt = [t for t in detected_clnt
                             if not t.isdigit() and t not in self.stopwords]
            return Counter(detected_clnt)

        def get_first(itrbl, predicate):
            '''Gets firts pair from @itrbl whose first item matches @predicate'''
            for item, count in itrbl:
                if item and predicate(item):
                    return (item, count)
            return (None, None)

        def contains_stopwords(s):
            for w in s.split():
                if w.lower() in self.stopwords:
                    return True


        # Count double-quoted occurences
        # print self.rawtext.encode('utf8', 'replace')
        quoted = [q.strip(' ()*,."\';:-/\\[]{}').encode('utf8', 'replace').strip(codecs.BOM_UTF8)
                  for q in quoted_re.findall(self.rawtext)]
        quoted = [lemmatize_unify_pronouns(q.lower()) for q in quoted
                  if q and len(q) < 50]
        quoted = [q for q in quoted
                  if not q.isdigit() and q not in self.stopwords]
        quoted_c = Counter(quoted + [s for s in quoted if not contains_stopwords(s)])
        # print 'QUOTED:', quoted_c.most_common()[:20]


        # Count occurences that appear in "between (..) and (..)" expressions
        conjunct = [q for q in betw_and_re.findall(self.rawtext)]
        conjunct = [w.strip('_-').lower() for w in pair_list_unpack(conjunct)]
        conjunct = [w for w in conjunct
                    if w and not w.isdigit() and w not in self.stopwords]
        conjunct_c = Counter(conjunct + [s for s in conjunct if not contains_stopwords(s)] * 3)
        # print 'BETWEEN:', conjunct_c.most_common()[:20]


        # Count occurences that appear after a "by" expressions
        byparty = [q for q in by_re.findall(self.rawtext)]
        byparty = [w.strip('_-').lower() for w in byparty]
        byparty = [w for w in byparty
                    if w and not w.isdigit() and w not in self.stopwords]
        byparty_c = Counter(byparty)# * 2)
        # print 'BY:', byparty_c.most_common()[:20]


        # Count words from "interesting" sentences
        liability_c = detected_sent_wcount(self.rawsentences, liability_re)
        between_c = detected_sent_wcount(self.rawsentences, between_re)
        rightreserve_c = detected_sent_wcount(self.rawsentences, rightreserve_re)
        provide_c = detected_sent_wcount(self.rawsentences, provide_re)

        # Final sum
        sum_c = (
            liability_c + between_c + rightreserve_c + provide_c +
            quoted_c + conjunct_c + byparty_c
        )

        # Half the counts for halfed_words
        for term in sum_c:
            if term in halfed_words:
                sum_c[term] /= 2

        # Significantly lower the counts for terms which contain stop words
        for term in sum_c:
            for word in term.split():
                if word in self.stopwords:
                    # Lower the count for each stopword in term
                    sum_c[term] /= 3

        ordered_sum_c = [(get_unicode(w), c) for w, c in sum_c.most_common()]

        # Try to collapse counts based on clusters
        if corefs:
            # Increase counts on the account of coreference detected mentions
            for clust in corefs:
                ordered_sum_c.append((lemmatize_unify_pronouns(clust.most_relevant().lower()), 3))
            ordered_sum_c =sorted(ordered_sum_c, key=itemgetter(1), reverse=True)

            clust_used = [False] * len(corefs)
            clust_reprez_idx = [-1] * len(corefs)
            collapsed_sum = []

            # Collapse counts for mentions found in the same cluster by coref
            for w, c in ordered_sum_c:
                for i, clust in enumerate(corefs):
                    if clust.fuzzy_match(w):
                        # Does this cluster already have a representative added
                        if clust_used[i]:
                            # Yes. Then just add current count to reprez's
                            idx = clust_reprez_idx[i]
                            reprez, old_c = collapsed_sum[idx]
                            collapsed_sum[idx] = (reprez, old_c + c)
                        else:
                            # No. Then add this as reprez
                            clust_used[i] = True
                            clust_reprez_idx[i] = len(collapsed_sum)
                            collapsed_sum.append((w, c))
                        break
                else:
                    # Not found in any cluster. Simply add it to the list
                    collapsed_sum.append((w, c))

            # Use the added counts
            ordered_sum_c = sorted(collapsed_sum, key=itemgetter(1), reverse=True)

        # Assign names to parties
        try:
            best1 = get_first(ordered_sum_c,
                              lambda x: x not in ['you', 'customer', 'member', 'client'])
            ordered_sum_c.remove(best1) # Remove it so that Party2 won't pick it
            party1 = best1[0]
            confidence1 = best1[1]
            p1_realform = Counter(ne_expand_re_fn(party1)
                                  .findall(self.rawtext)).most_common()[0][0]
        except:
            party1 = ''
            p1_realform = ''
            confidence1 = 0
        try:
            best2 = get_first(ordered_sum_c,
                              lambda x: x not in p1_realform.lower())
            party2 = best2[0]
            confidence2 = best2[1]
            p2_realform = Counter(ne_expand_re_fn(party2)
                                  .findall(self.rawtext)).most_common()[0][0]
        except:
            party2 = ''
            p2_realform = ''
            confidence2 = 0


        # print party1
        # print Counter(ne_expand_re_fn(party1).findall(self.rawtext)).most_common()[:5]
        # print party2
        # print Counter(ne_expand_re_fn(party2).findall(self.rawtext)).most_common()[:5]
        # print '~' * 40

        p1_realform = party_bad_chars_re.sub('', p1_realform)
        p2_realform = party_bad_chars_re.sub('', p2_realform)

        return (
            truncate(p1_realform, 35), # Them
            truncate(p2_realform, 35), # You
            (confidence1, confidence2)
        )
