# -*- coding: utf-8 -*-

import re
import collections

from nltk import pos_tag
from nltk import Tree
from nlplib.tokenizing.splitta.splitta import splitta_word_tokenize as word_tokenize
from unidecode import unidecode


LINEBREAK_MARKER = '__/BR/__'
INDENTLEVEL_MARKER = '__/ILVL/%d/__'
INDENTLEVEL_MARKER_RE = '__/ILVL/[0-9]+?/__'
INDENTLEVEL_MARKER_CAPTURE_RE = '__/ILVL/([0-9]+?)/__'
indentlevel_re = re.compile(INDENTLEVEL_MARKER_RE)
indentlevel_capture_re = re.compile(INDENTLEVEL_MARKER_CAPTURE_RE)
NUMBERING_MARKER = '__/NBR/%s/__'
NUMBERING_MARKER_RE = '__/NBR/.+?/__'
NUMBERING_MARKER_CAPTURE_RE = '__/NBR/(.+?)/__'
numbering_re = re.compile(NUMBERING_MARKER_RE)
numbering_capture_re = re.compile(NUMBERING_MARKER_CAPTURE_RE)

number_re = re.compile(r'\b([0-9]+[,.]?)+\b')
fillin_underscore_re = re.compile(r'\b(_+)\b')

ws_re = re.compile(r'\s+')

quoted_re = re.compile(r'\"[a-zA-Z0-9_\.*#$%@~&\({\[<][a-zA-Z0-9 \-_\.*#$%@~&\(\){}\[\]/\\<>]+\"')
unicode_quote_re = re.compile(ur'([“”]|\xe2\x80\x9d|\xe2\x80\x9c)+', re.UNICODE)
betw_and_re = re.compile(r'between (?:the )?([\w_"\-]+) and (?:the )?([\w_"\-]+)', re.IGNORECASE)
by_re = re.compile(r'(?: |\n)by (?!the)(?!any)([^ .,]+)', re.IGNORECASE)

# Define "interesting" sentences
liability_re = re.compile(r'(be |not )?(be held )?(liable|responsible|obligated)', re.IGNORECASE)
rightreserve_re = re.compile(r'reserves? (the )?right', re.IGNORECASE)
between_re = re.compile(r' between ', re.IGNORECASE)
provide_re = re.compile(r'(must|shall|will|may) (not |also )?(provide)', re.IGNORECASE)

ne_expand_re_fn = lambda start: \
    re.compile('(' + r'(?:[A-Z0-9",&][\w0-9_"\-.,]* )*' + ''.join(['[%s%s]' % (l, l.upper()) for l in start]) + r'(?: [A-Z0-9",&][\w0-9_"\-.,]*)*)')

party_bad_chars_re = re.compile(r'[\[({<.,;:#>})\]]+')

TLDS = ("com net org mil edu biz ch at ru de tv io ai gov "
        "st br fr nl dk ar jp eu it es us ca pl co ro ly "
        "xxx cat int pro tel aero info name coop asia mobi").split()


STANDARD_ENTITY_NOTATIONS = (
    'ltd.', 'ltd', 'Ltd.', 'Ltd', 'LTD', 'LTD.',
    'inc.', 'inc', 'Inc.', 'Inc', 'INC', 'INC.',
    'Limited',
    'llc', 'LLC', 'Llc',
    'GmbH',
    'ApS',
    'UK',
    'US',
    'U.G.',
    'Co.',
    'Corporation',
    'Software', 'software',
    'Communications', 'communications',
    'L.P.',
    'Company',
    'c/o',
    'C/O',
    'pty', 'Pty', 'PTY',
)


STANDARD_DETERMINERS = (
    'a',
    'an',
    'the',
    'that',
    'neither',
    'what',
    'these',
    'those',
    'either',
)


def prepare_company_name(company_name):
    company_name = ' ' + company_name + ' '
    for rem in STANDARD_ENTITY_NOTATIONS:
        company_name = company_name.replace(' ' + rem + ' ', ' ')

    for rem in ['.', ',', '"']:
        company_name = company_name.replace(rem, '')

    company_name = re.sub('\s+', ' ', company_name).strip()

    return company_name


def remove_determiners(name):
    name = ' ' + re.sub('\s+', ' ', name).strip() + ' '
    for rem in STANDARD_DETERMINERS:
        for remf in basic_forms(rem):
            if ' ' + remf + ' ' in name:
                name = name.replace(' ' + remf + ' ', ' ')

    return name.strip()


def basic_forms(form):
    lower = form.lower()
    upper = form.upper()
    if not lower:
        return lower
    capitalized = lower[0].upper() + lower[1:]

    return list(set([capitalized, lower, upper]))


def tagged2wordtag(tagged_sentence):
    """
    Convert a NLTK tagged sentence [(word, tag), ...]
    to this format [(word, word__tag), ...]
    """
    return [(tt[0], tt[0] + '__' + tt[1]) for tt in tagged_sentence]


def wordtag2tagged(wordtagged_sentence):
    """
    Convert a tagged sentence in this format: [(word, word__tag), ...]
    to classic NLTK format: [(word, tag), ...]
    """
    return [(wtt[0], wtt[1].split('__')[1]) for wtt in wordtagged_sentence]


def lemmatize_unify_pronouns(w):
    '''
    Reduces forms like "your" to the basic form.
    Handles only first and second persons.
    '''
    lemmas = {
        'we': 'us',
        'myself': 'us',
        'ourselves': 'us',
        'mine': 'us',
        'our': 'us',
        'ours': 'us',
        'me': 'us',
        'my': 'us',
        'yourself': 'you',
        'yourselves': 'you',
        'yours': 'you',
        'your': 'you',
        'theirselves': 'they',
        'theirs': 'they',
        'their': 'they',
        'them': 'they',
    }
    if w.lower() in lemmas:
        return lemmas[w.lower()]
    return w


def get_unicode(strOrUnicode, encoding='utf-8'):
    def __if_number_get_string(number):
        converted_str = number
        if isinstance(number, int) or \
           isinstance(number, float):
            converted_str = str(number)
        return converted_str

    strOrUnicode = __if_number_get_string(strOrUnicode)
    if isinstance(strOrUnicode, unicode):
        return strOrUnicode
    return unicode(strOrUnicode, encoding, errors='ignore')


halfed_words = [
    'provider',
    'supplier',
    'supply',
    'subject',
    'received',
    'entire',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
]

# Stopwords
nonPR_stopwords = ['kind', 'and/or', 'http', 'other', 'others', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'whether', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'many', '``', "''", ',', ':', 'also', 'thus', 'shall', 'without', 'either', 'neither', 'hereafter', 'hereto']
nonPR_stopwords += ['third', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves']
legal_specific_words = [
    'respect',
    'policy',
    'policies',
    'copyright',
    'right',
    'rights',
    'author',
    'authors',
    'associated',
    'connection',
    'connections',
    'service',
    'services',
    'solution',
    'solutions',
    'platform',
    'platforms',
    'document',
    'documents',
    'premium',
    'website',
    'websites',
    'web',
    'site',
    'sites',
    'software',
    'information',
    'installer',
    'contract',
    'contracts',
    'terms',
    'license',
    'licenses',
    'tos/eula',
    'tou/eula',
    'eula',
    'msa',
    'nda',
    'agreement',
    'agreements',
    'account',
    'accounts',
    'data',
    'content',
    'dealership',
    'game',
    'games',
    'entity',
    'entities',
    'product',
    'products',
    'companies',
    'business',
    'employer',
    'employers',
    'employee',
    'employees',
    'provide',
    'provides',
    'provided',
    'providers',
    'impose',
    'imposed',
    'imposes',
    'make',
    'makes',
    'made',
    'access',
    'asset',
    'discussion',
    'resolve',
    'resolved',
    'maintain',
    'maintained',
    'related',
    'arising',
    'liable',
    'liability',
    'responsible',
    'acknowledge',
    'program',
    'programs',
    'based',
    'law',
    'legal',
    'limited',
    'bargain',
    'licensee',
    'licensed',
    'professional',
    'including',
    'claim',
    'claims',
    'matter',
    'matters',
    'suppliers',
    'licensors',
    'failure',
    'property',
    'properties',
    'bodily',
    'injury',
    'damage',
    'damages',
    'breach',
    'breaches',
    'terminate',
    'terminates',
    'terminated',
    'loss',
    'losses',
    'lost',
    'interruption',
    'cover',
    'covers',
    'cost',
    'costs',
    'whatsoever',
    'consequential',
    'indirect',
    'example',
    'exemplary',
    'special',
    'punative',
    'incidental',
    'negligence',
    'profit',
    'profits',
    'revenue',
    'savings',
    'economic',
    'limitation',
    'limitations',
    'event',
    'events',
    'agree',
    'agrees',
    'prohibit',
    'prohibits',
    'prohibited',
    'use',
    'using',
    'misusing',
    'uses',
    'user',
    'users',
    'user-generated',
    'end-user',
    'inability',
    'reserved',
    'reserve',
    'reserves',
    'even',
    'advised',
    'possibility',
    'possibilities',
    'report',
    'reports',
    'party',
    'parties',
    'material',
    'materials',
    'fee',
    'fees',
    'arbitration',
    'online',
    'confidential',
    'confidential information',
    'confidentiality',
    'proprietary',
    'purpose',
    'as-is',
    'place',
    'written',
    'disclose',
    'disclosed',
    'disclosure',
    'feedback',
    'dispute',
    'notice',
]


def remove_linebreak_markers(text):
    """ Actually turns them into spaces """
    return text.replace(LINEBREAK_MARKER, ' ')

def linebreaks_to_markers(text):
    bslashn_text = text.replace('\r\n', '\n')        # Handle Win
    bslashn_text = bslashn_text.replace('\r', '\n')  # Handle OSX
    return bslashn_text.replace('\n', LINEBREAK_MARKER)

def markers_to_linebreaks(text):
    return text.replace(LINEBREAK_MARKER, '\n')


def preformat_markers(text):
    # Convert line-break markers to usual line-break characters
    text = markers_to_linebreaks(text)

    # Convert indent-level markers to proper indents
    text = indentlevel_capture_re.sub(
        # Use 2 additional spaces per each nested indent-level
        lambda match: ' ' * 2 * int(match.group(1)), text
    )

    # Convert numbering markers to proper numbers
    text = numbering_capture_re.sub(r'\1 ', text)

    return text


all_roman_re = re.compile(r'[ivxIVX]+$')
abc_bullet_re = re.compile(r'[a-zA-Z]$')
digit_bullet_re = re.compile(r'([0-9]+\.)*[0-9]+$')
quotes = u'"\'“”'
non_sentence_ends = [
    'inc.', 'ltd.', 'llc.',
    'et.', 'al.', 'etc.',
    'mr.', 'ms.', 'mrs.',
    'u.s.',
]


def is_bullet(s):
    if not s.endswith('.'):
        return False
    s = s[:-1]
    return any([all_roman_re.match(s),
                abc_bullet_re.match(s),
                digit_bullet_re.match(s)])


def is_abbreviation(s_p, s, s_n):
    """
    Checks whether the word `s` is an abbreviation using its context,
    i.e. the previous word `s_p` and the next word `s_n`.
    """

    # No length restriction by default
    def _is_name(s, max_len=float('inf')):
        s = s.strip('.,:;')
        return 0 < len(s) <= max_len and s[0].isupper() and s.isalpha()

    # Name abbreviation, e.g. John D. Smith
    if _is_name(s_p) and _is_name(s, max_len=1) and _is_name(s_n):
        return True

    # Other special cases

    if s == 'v.':
        return True

    if (s, s_n) == ('U.', 'S.'):
        return True

    return False


def is_non_sentence_end(s):
    s = s.strip(quotes).lower()
    return s in non_sentence_ends


def merge_bad_sentsplits(sentences):
    """ Merge special cases (e.g. bullets) of unwanted splits. """

    def _merge_two(sent, sent_after):
        to_merge = False
        if sent_after.strip() == '':
            to_merge = True
        else:
            toks = sent.strip().split('\n')[-1].split()
            if len(toks) > 0:
                if len(toks) == 1 and is_bullet(toks[0]):
                    to_merge = True
                elif is_non_sentence_end(toks[-1]):
                    to_merge = True
                elif len(toks) > 1:
                    toks_after = sent_after.strip().split('\n')[0].split()
                    if len(toks_after) > 0:
                        to_merge = is_abbreviation(toks[-2], toks[-1], toks_after[0])

        if to_merge:
            return [sent + sent_after]
        return [sent, sent_after]

    # Merge the unwanted splits
    merged = sentences[:1]
    for sent_after in sentences[1:]:
        sent = merged.pop()
        merged.extend(_merge_two(sent, sent_after))
    return merged


sentence_split_re = re.compile(
    ur'((?<=[^A-Z].[.?!])\s+(?=[A-Z])|(?<=[^A-Z].[.?!])\s*[\n\r]+|[\n\r]\s*[\n\r]+|'
    # Those 2 again for the case of <Text "quoted." New sent.>
    ur'(?<=[^A-Z].[.?!]["\'“”])\s+(?=[A-Z])|(?<=[^A-Z].[.?!]["\'“”])\s*[\n\r]+|[\n\r]\s*[\n\r]+|'
    # And the case of ALL-CAPS
    ur'(?<=[^a-z][.?!])\s+(?=[A-Z])|(?<=[^a-z][.?!])\s*[\n\r]+|[\n\r]\s*[\n\r]+)',
    re.UNICODE
)


def is_title(sentence):
    """
    Checks whether a sentence looks like a title.

    A title may be defined as several capitalized words, possibly separated
    with some conjunctions, determiners or prepositions. Bullets at the
    beginning of the sentence are allowed, but they aren't counted as words.
    Punctuation characters at the end aren't allowed.

    A (non-empty) sentence is considered to be a title, if it consists at most
    MAX_MAIN_WORDS_COUNT capitalized words (containing the main meaning,
    i.e. "main" words). In addition to the "main" words, some "auxiliary"
    (i.e. non-capitalized) words are also allowed, but only if they are short
    enough (i.e. up to MAX_AUX_WORD_LENGTH characters in length). The
    "auxiliary" words are assumed to be some conjunctions, determiners or
    prepositions.

    E.g.: "Terms of Service", "Terms of Use", etc.
    """
    MAX_MAIN_WORDS_COUNT = 4
    MAX_AUX_WORD_LENGTH = 4

    sentence = sentence.strip()
    if not sentence:
        return False
    if sentence[-1] in (',', ';', ':'):
        return False
    capitalized_words_count = 0
    words = sentence.split()
    for index, word in enumerate(words):
        if index == 0 and is_bullet(word):
            continue
        if word[0].isupper():  # "main" word
            capitalized_words_count += 1
        elif len(word) <= MAX_AUX_WORD_LENGTH:  # "auxiliary" word
            continue
        else:
            return False
    return 1 <= capitalized_words_count <= MAX_MAIN_WORDS_COUNT


def split_sentences(text):
    """
    Splits a block of plain text into sentences (boundaries are captured too).
    """

    sentences = sentence_split_re.split(text)
    sentences = merge_bad_sentsplits(sentences)
    # Try to additionally split sentences with titles
    sentences_with_titles = []
    for sentence in sentences:
        left_part, _, right_part = sentence.strip().partition('\n')
        if right_part and is_title(left_part):
            # Preserve original indentation
            index = sentence.find(left_part)
            left_part, right_part = (sentence[:index + len(left_part) + 1],
                                     sentence[index + len(left_part) + 1:])
            sentences_with_titles.append(left_part)
            sentences_with_titles.append(right_part)
        else:
            sentences_with_titles.append(sentence)
    return sentences_with_titles


def preprocess_text(text):
    """ Clean some common dirt from text """
    to_replace = [
        (u'‹', ' < '),
        (u'›', ' > '),
        (u'«', ' < '),
        (u'»', ' > '),
        (u'≤', ' < '),
        (u'≥', ' > '),
        ('"', ' " '),
        (u'’', "'"),
        (u'`', "'"),
        (u" '", " ' "),
        (u"' ", " ' "),
        ('[', '('),
        (']', ')'),
        ('<', '('),
        ('>', ')'),
        ('{', '('),
        ('}', ')'),
        ('(', ' _LPAR_ '),
        (')', ' _RPAR_ '),
    ]

    text = unicode_quote_re.sub('"', text)
    for before, after in to_replace:
        text = text.replace(before, after)

    text = ws_re.sub(' ', text)
    return unidecode(text.strip())

# TODO: This should be obsolete
def postprocess_text(text):
    to_replace = [
        ('_LPAR_', '('),
        ('_RPAR_', ')'),

        (' ,', ','),
        (' :', ':'),
        (' ;', ';'),
        (' .', '.'),
        (' %', '%'),
        (' )', ')'),
        ('( ', '('),
        (' \'s ', '\'s '),
    ]
    for before, after in to_replace:
        text = text.replace(before, after)

    return text.strip()


def text2wordtag(text):
    """ Convert a raw text to word-tagged format """
    sentences = split_sentences(text)
    return sents2wordtag(sentences)


def sents2wordtag(sentences):
    """ Convert list of raw sentences to word-tagged format """

    def _pos_tag(ts):
        """
        Empty words lead to errors in the current version of NLTK,
        so simply filter them out before applying the actual `pos_tag` function.

        A sample error message from IPython:
            .../nltk/tag/perceptron.py in normalize(self, word)
            --> 240         elif word[0].isdigit():
            IndexError: string index out of range
        """
        if '' in ts:
            ts = [w for w in ts if w]
        return pos_tag(ts)

    tokenized_sentences = [word_tokenize(s) for s in sentences]
    tagged_sentences = [_pos_tag(ts) for ts in tokenized_sentences]
    return [tagged2wordtag(ts) for ts in tagged_sentences]


def tree2str(t):
    """ Convert a Tree node to a python string """
    return ' '.join(tree2str(node) if isinstance(node, Tree)
                                   else node[0] for node in t)


def extract_nodes(tree, label=None, predicate=None):
    """
    Perform a DFS search and create a list of Tree nodes
    that have either the label equal to `label`
    or they satisfy `predicate`
    """
    results = []
    for node in tree:
        if isinstance(node, Tree):
            if label is not None and node.label() == label:
                results.append(node)
            elif predicate is not None and predicate(node):
                results.append(node)
            else:
                results.extend(extract_nodes(node, label, predicate))
    return results


class IdGenerator:
    """
    Generate an unique ID. The unique IDs can be bucketed by `label`
    """
    tracker = collections.defaultdict(int)

    @classmethod
    def get(cls, label=''):
        value = cls.tracker[label]
        cls.tracker[label] += 1
        return value


# person/number/gender
hPers = {'i':           (1,     'singular',     'unknown'),
         'you':         (2,     'unknown',      'unknown'),
         'he':          (3,     'singular',     'masculine'),
         'she':         (3,     'singular',     'feminine'),
         'it':          (3,     'singular',     'neutral'),
         'we':          (1,     'plural',       'unknown'),
         'they':        (3,     'plural',       'unknown'),
         'myself':      (1,     'singular',     'unknown'),
         'yourself':    (2,     'singular',     'unknown'),
         'himself':     (3,     'singular',     'masculine'),
         'herself':     (3,     'singular',     'feminine'),
         'itself':      (3,     'singular',     'neutral'),
         'ourselves':   (1,     'plural',       'unknown'),
         'yourselves':  (2,     'plural',       'unknown'),
         'themselves':  (3,     'plural',       'unknown'),
         'mine':        (1,     'singular',     'unknown'),
         'yours':       (2,     'unknown',      'unknown'),
         'your':        (2,     'unknown',      'unknown'),
         'hers':        (3,     'singular',     'feminine'),
         'his':         (3,     'singular',     'masculine'),
         'its':         (3,     'singular',     'neutral'),
         'ours':        (1,     'plural',       'unknown'),
         'our':         (1,     'plural',       'unknown'),
         'theirs':      (3,     'plural',       'unknown'),
         'their':       (3,     'plural',       'unknown'),
         'me':          (1,     'singular',     'unknown'),
         'him':         (3,     'singular',     'masculine'),
         'her':         (3,     'singular',     'feminine'),
         'us':          (1,     'plural',       'unknown'),
         'them':        (3,     'plural',       'unknown'),
}


def fuzzy_pronoun_match(pronoun1, pronoun2, check_number=False):
    """
    Match pronouns ignoring the inflectioned forms (Ex: you, yours, your)
    params:
    `pronoun1` -- str (the actual form of the pronoun)
    `pronoun2` -- str (the actual form of the pronoun)
    `check_number` -- bool (ignore matching by number)
    """
    pronoun1 = pronoun1.lower().strip()
    pronoun2 = pronoun2.lower().strip()
    if pronoun1 not in hPers or pronoun2 not in hPers:
        return False

    if hPers[pronoun1][0] != hPers[pronoun2][0]:
        return False

    if check_number:
        number1 = hPers[pronoun1][1]
        number2 = hPers[pronoun2][1]

        if number1 != number2 and 'unknown' not in [number1, number2]:
            return False

    gender1 = hPers[pronoun1][2]
    gender2 = hPers[pronoun2][2]

    if gender1 != gender2 and 'unknown' not in [gender1, gender2]:
        return False

    return True


def extract_mentions(text):
    return set(re.findall("@([a-z0-9_]+)", text, re.I))
