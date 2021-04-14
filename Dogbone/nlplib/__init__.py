
from nlplib.facade import NlplibFacade
from nlplib.utils import LINEBREAK_MARKER


def process_rawtext(raw_text):
    from nlplib.utils import split_sentences
    sentences = split_sentences(raw_text)
    analysis, facade = doclevel_process(sentences)
    sent_level = sentlevel_process(facade)
    analysis.update(sent_level)
    return analysis


def doclevel_process(text=None, sentences=None):
    norm_confid = lambda x: min(100, int((x / 14.)**2 * 100))

    facade = NlplibFacade(text=text, sentences=sentences)

    them_party, you_party, confidence = facade.parties
    them_confid, you_confid = list(map(norm_confid, confidence))

    parties_information = {
        'them': {
            'name': them_party,
            'confidence': them_confid,
        },
        'you': {
            'name': you_party,
            'confidence': you_confid,
        }
    }

    analysis = {'parties': parties_information}

    return analysis, facade


# TODO: Move this inside facade, that's the purpose of facade, to hide complexity
def sentlevel_process(text=None, sentences=None, parties=None, user=None):
    facade = NlplibFacade(text=text, sentences=sentences, parties=parties)

    them_party, you_party, confidence = facade.parties

    party_translation_dict = {
        'both': 'both',
        you_party: 'you',
        them_party: 'them',
    }

    # Everything should be enabled by default (unless explicitly disabled)
    rlte_flags = user.details.rlte_flags if user else {}

    clauses = []

    # Run each of RLT analyzers (if enabled)
    for party in party_translation_dict:
        if rlte_flags.get('responsibilities', True):
            resps = facade.responsibilities(party)
            clauses.append(
                ('RESPONSIBILITY', resps, party)
            )
        if rlte_flags.get('liabilities', True):
            liabs = facade.liabilities(party)
            clauses.append(
                ('LIABILITY', liabs, party)
            )
        if rlte_flags.get('terminations', True):
            terms = facade.terminations(party)
            clauses.append(
                ('TERMINATION', terms, party)
            )

    analysis = {'sentences': [{'form': s, 'idx': i}
                              for i, s in enumerate(facade.processed_text)]}

    # Extract references (if enabled)
    if rlte_flags.get('external_references', True):
        references = [{'form': er.form, 'reftype': er.reftype[1],
                       'offset': er.pos_start, 'length': len(er.form),
                       'sent_idx': er.sent_idx}
                      for er in facade.external_references]

        for i, sentence in enumerate(analysis['sentences']):
            # Add references found in the current sentence
            sentence['external_refs'] = [r for r in references
                                         if r['sent_idx'] == i]

    for label, index, party in clauses:
        for sentence_idx, sublabel in index.items():
            if 'annotations' not in analysis['sentences'][sentence_idx]:
                analysis['sentences'][sentence_idx]['annotations'] = []

            analysis['sentences'][sentence_idx]['annotations'].append(
                {'label': label,
                 'sublabel': sublabel,
                 'party': party_translation_dict[party]}
            )

    return analysis, facade
