# -*- coding: utf-8 -*-

import nltk
import re
from tokenizing.splitta.splitta import splitta_sent_tokenize as sent_tokenize
from tokenizing.splitta.splitta import splitta_word_tokenize as word_tokenize
from nltk.stem import WordNetLemmatizer


pattern = """
              NP:     {<CD>?<JJ><,><NNP>+}
                      {<DT|PP\$>?<JJ>*<NN\S>+}
                      {<DT|PP\$>?<JJ>*<NN>+}
                      {<JJR><NN\S>}
                      {<CD><NNP\S>+<NN\S>}
                      {<VBN><NN\S>+}
                      {<NNP\S>+}

              """


def get_regex_chunker():
    return nltk.RegexpParser(pattern)


def preprocess_mention(mention):
    to_replace = {
        '.': ' ',
        '\xe2\x80\x9d': ' " ',
        '\xe2\x80\x9c': ' " ',
        '\xe2\x80\x99': '\'',
        '(': ' ',
        ')': ' ',
        '[': ' ',
        ']': ' ',
        '{': ' ',
        '}': ' ',
        '"': ' " ',
    }

    for tr in to_replace:
        mention = mention.replace(tr, to_replace[tr]).strip()

    mention = re.sub(' +', ' ', mention)
    return mention


def get_mentions(tagged_sentences, np_chunker):
    lemmatizer = WordNetLemmatizer()
    mentions = []
    for idx, sent in enumerate(tagged_sentences):
        pronouns = [t for t in sent if t[1].startswith('P')]
        for pronoun in pronouns:
            form = pronoun[0]
            form_lower = form.lower()
            pos = pronoun[1]
            mentions.append({'form': form,
                             'pos': pos,
                             'sentence': idx,
                             'person': hPers[form_lower][0] if form_lower in hPers else 'unknown',
                             'number': hPers[form_lower][1] if form_lower in hPers else 'unknown',
                             'gender': hPers[form_lower][2] if form_lower in hPers else 'unknown',
                             'head': form,
                             'lemma': form_lower})


        np_phrases = [t for t in np_chunker.parse(sent) if isinstance(t, nltk.Tree)]

        for np in np_phrases:
            form = preprocess_mention(' '.join([t[0] for t in np]))
            if len(form) <= 2:
                continue
            form_lower = form.lower()

            head_token = None
            for token in reversed(np):
                if token[1].startswith('N'):
                    head_token = token

            head = head_token[0] if head_token else 'unknown'
            pos = head_token[1] if head_token else 'unknown'

            number = 'unknown'
            if pos != 'unknown':
                number = 'plural' if pos.endswith('S') else 'singular'

            person = 'unknown'
            gender = 'unknown'

            mentions.append({'form': form,
                             'pos': pos,
                             'sentence': idx,
                             'person': person,
                             'number': number,
                             'gender': gender,
                             'head': head,
                             'lemma': lemmatizer.lemmatize(head)})
    return mentions


def init_chains(mentions):
    return [[m] for m in mentions]


def merge_chains(chains, merges):
    reversed_merges = reversed(merges)

    for merge in reversed_merges:
        to_idx, from_idx = merge
        chains[to_idx] += chains[from_idx]

    for merge in sorted(list(set([merge[1] for merge in merges])), reverse=True):
        del chains[merge]

    return chains


def string_match_sieve(chains):
    merges = []

    for source_idx in range(len(chains) - 1):
        for target_idx in range(source_idx + 1, len(chains)):
            source_forms = [m['form'].lower() for m in chains[source_idx]]
            target_forms = [m['form'].lower() for m in chains[target_idx]]

            for sf in source_forms:
                if sf in target_forms:
                    merges.append((source_idx, target_idx))
                    break

    return merge_chains(chains, merges)


def pronoun_person_sieve(chains):
    merges = []

    for source_idx in range(len(chains) - 1):
        source_pronouns = [m for m in chains[source_idx] if m['pos'].startswith('P')]
        for target_idx in range(source_idx + 1, len(chains)):
            target_pronouns = [m for m in chains[target_idx] if m['pos'].startswith('P')]

            for sp in source_pronouns:
                try:
                    person, number, gender = hPers[sp['lemma']]
                    viable_candidates = [tp for tp in target_pronouns if tp['person'] == person]
                    viable_candidates = [vc for vc in viable_candidates if vc['number'] == number
                                                                            or (vc['lemma'][:3] == 'you'
                                                                            and sp['lemma'][:3] == 'you')]
                    viable_candidates = [vc for vc in viable_candidates if vc['gender'] == gender
                                                                        or gender == 'unknown'
                                                                        or vc['gender'] == 'unknown']
                    if viable_candidates:
                        merges.append((source_idx, target_idx))
                        break
                except Exception as e:
                    pass

    return merge_chains(chains, merges)


def flexible_string_match_string(chains):
    merges = []

    for source_idx in range(len(chains) - 1):
        for target_idx in range(source_idx + 1, len(chains)):
            source_forms = [m['form'].lower() for m in chains[source_idx]]
            target_forms = [m['form'].lower() for m in chains[target_idx]]

            source_heads = [m['head'].lower() for m in chains[source_idx]]
            target_heads = [m['head'].lower() for m in chains[target_idx]]

            for sh in source_heads:
                if any([' ' + sh + ' ' in ' ' + tf + ' ' for tf in target_forms]):
                    merges.append((source_idx, target_idx))
                    break

            for th in target_heads:
                if any([' ' + th + ' ' in ' ' + sf + ' ' for sf in source_forms]):
                    merges.append((source_idx, target_idx))
                    break

    return merge_chains(chains, merges)





text = """
End-User License Agreement

END-USER LICENSE AGREEMENT FOR “GIELTSHELP.COM” and “ACADEMICENGLISHHELP.COM” IMPORTANT PLEASE READ THE TERMS AND CONDITIONS OF THIS LICENSE AGREEMENT CAREFULLY BEFORE CONTINUING WITH ANY PRODUCT AND/OR SERVICE: 2THINK1 SOLUTIONS INC’s End-User License Agreement (“EULA”) is a legal agreement between you (either an individual or a single entity) and 2THINK1 SOLUTIONS INC for the 2THINK1 SOLUTIONS INC SOFTWARE PRODUCT(S) AND/OR WEBSITES identified above which may include associated software components, media, printed materials, and “online” or electronic documentation (“SOFTWARE PRODUCT(S) AND/OR WEBSITES”). By installing, copying, or otherwise using the SOFTWARE PRODUCT(S) AND/OR WEBSITES, you agree to be bound by the terms of this EULA. This license agreement represents the entire agreement concerning the program between you, 2THINK1SOLUTIONS INC, (referred to as “licenser”), and it supersedes any prior proposal, representation, or understanding between the parties. If you do not agree to the terms of this EULA, do not install or use the SOFTWARE PRODUCT(S) AND/OR WEBSITES. The SOFTWARE PRODUCT(S) AND/OR WEBSITES is protected by copyright laws and international copyright treaties, as well as other intellectual property laws and treaties. The SOFTWARE PRODUCT(S) AND/OR WEBSITES is licensed, not sold.
1. GRANT OF LICENSE.

The SOFTWARE PRODUCT(S) AND/OR WEBSITES is licensed as follows:
(a) Installation and Use.
2THINK1 SOLUTIONS INC grants you the right to install and use copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES on your computer running a validly licensed copy of the operating system for which the SOFTWARE PRODUCT(S) AND/OR WEBSITES was designed [e.g., Windows 95, Windows NT, Windows 98, Windows 2000, Windows 2003, Windows XP, Windows ME, Windows Vista].
(b) Backup Copies.
You may also make copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES as may be necessary for backup and archival purposes.
2. DESCRIPTION OF OTHER RIGHTS AND LIMITATIONS.

(a) Maintenance of Copyright Notices.
You must not remove or alter any copyright notices on any and all copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
(b) Distribution.
You may not distribute registered copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES to third parties. Evaluation versions available for download from 2THINK1 SOLUTIONS INC’s websites may be freely distributed.
(c) Prohibition on Reverse Engineering, Decompilation, and Disassembly.
You may not reverse engineer, decompile, or disassemble the SOFTWARE PRODUCT(S) AND/OR WEBSITES, except and only to the extent that such activity is expressly permitted by applicable law notwithstanding this limitation.
(d) Rental.
You may not rent, lease, or lend the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
(e) Support Services.
2THINK1 SOLUTIONS INC may provide you with support services related to the SOFTWARE PRODUCT(S) AND/OR WEBSITES (“Support Services”). Any supplemental software code provided to you as part of the Support Services shall be considered part of the SOFTWARE PRODUCT(S) AND/OR WEBSITES and subject to the terms and conditions of this EULA.
(f) Compliance with Applicable Laws.
You must comply with all applicable laws regarding use of the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
3. TERMINATION
"""

if __name__ == '__main__':
    raw_sents = sent_tokenize(text)
    tokenized_sents = [word_tokenize(s) for s in raw_sents]
    tagged_sents = [nltk.pos_tag(ts) for ts in tokenized_sents]

    mentions = get_mentions(tagged_sents, get_regex_chunker())

    for m in mentions:
        print(m['form'])

    chains = init_chains(mentions)
    print('Finished init_chains')
    # print "NUMBER OF CHAINS:", len(chains)
    # print '============================================'

    chains = string_match_sieve(chains)
    print('Finished string_match_sieve')
    # print 'AFTER "string_match_sieve"'
    # print '============================================'
    # print "NUMBER OF CHAINS:", len(chains)
    # for chain in chains:
    #     print [m['form'] for m in chain[:10]]


    chains = pronoun_person_sieve(chains)
    print('Finished pronoun_person_sieve')
    # print 'AFTER "pronoun_person_sieve"'
    # print '============================================'
    # print "NUMBER OF CHAINS:", len(chains)
    # for chain in chains:
    #     print [m['form'] for m in chain[:10]]


    # chains = flexible_string_match_string(chains)
    # print 'Finished flexible_string match_string'
    # print 'AFTER "flexible_string_match_string"'
    # print '============================================'
    # print "NUMBER OF CHAINS:", len(chains)
    for chain in chains:
        print([m['form'] for m in chain[:10]])