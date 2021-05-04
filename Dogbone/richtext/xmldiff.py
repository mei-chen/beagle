import copy
import datetime
from html.parser import HTMLParser
import pydiff
import pytz
import re
import time
from bs4 import BeautifulSoup
from collections import defaultdict, deque
from dateutil.parser import parse as date_parse
from xml.sax.saxutils import unescape as xml_unescape

from django.contrib.auth.models import User
from nlplib.utils import (INDENTLEVEL_MARKER, NUMBERING_MARKER,
                          INDENTLEVEL_MARKER_RE, NUMBERING_MARKER_RE,
                          indentlevel_re, numbering_re,
                          markers_to_linebreaks)
from django.utils import timezone
from utils.functional import first as find_first


html = HTMLParser()


DOCX_DOCUMENT_FNAME = 'word/document.xml'
DOCX_STYLES_FNAME = 'word/styles.xml'
DOCX_NUMBERING_FNAME = 'word/numbering.xml'
DOCX_COMMENTS_FNAME = 'word/comments.xml'
DOCX_CONTENTTYPES_FNAME = '[Content_Types].xml'
DOCX_RELS_FNAME = 'word/_rels/document.xml.rels'
DOCX_SETTINGS_FNAME = 'word/settings.xml'
ANNOTATION_IMG_NAME = 'beagle-logo_vector_tiny.png'


# Tags for XML token types (the shorter, the less db space used)
OPEN = 'o'
CLOSE = 'c'
TEXT = 't'
DELETED_TEXT = 'dt'
OTHER_TEXT = 'ot'
MARKER = 'm'


TEXT_TYPES = (TEXT, DELETED_TEXT, OTHER_TEXT)


# Special markers around deleted/inserted XML nodes (instead of w:del/w:ins tags)
DELETION = 'd'
INSERTION = 'i'


txttag_re = re.compile(r'w:t\b')
xml_style_val_re = re.compile(r'w:val="?([^"/]+)')


def get_val_attr(tx):
    try:
        return xml_style_val_re.search(tx).group(1)
    except:
        pass


comment_start_re = re.compile(r'commentRangeStart w:id="(\d+)"')
comment_end_re = re.compile(r'commentRangeEnd w:id="(\d+)"')
user_mention_re = re.compile(r'@\[(.+?)\]\((.+?)\)')


def is_para_node(tx):
    return (tx == 'w:p' or tx == 'w:p/' or tx.startswith('w:p '))
def is_parastyle_node(tx):
    return (tx == 'w:pPr' or tx.startswith('w:pPr '))
def is_run_node(tx):
    return (tx == 'w:r' or tx.startswith('w:r '))
def is_runstyle_node(tx):
    return (tx == 'w:rPr' or tx.startswith('w:rPr '))
def is_text_node(tx):
    return (tx == 'w:t' or tx.startswith('w:t '))
def is_named_parastyle_node(tx):
    return (tx == 'w:pStyle' or tx.startswith('w:pStyle '))
def is_named_runstyle_node(tx):
    return (tx == 'w:rStyle' or tx.startswith('w:rStyle '))
def is_style_size_node(tx):
    return (tx == 'w:sz' or tx.startswith('w:sz ')) or \
           (tx == 'w:szCs' or tx.startswith('w:szCs '))
def is_style_bold_node(tx):
    return (tx == 'w:b' or tx == 'w:b/' or tx.startswith('w:b '))
def is_style_underline_node(tx):
    return (tx == 'w:u' or tx == 'w:u/' or tx.startswith('w:u '))
def is_indentlevel_node(tx):
    return (tx == 'w:ilvl' or tx.startswith('w:ilvl '))
def is_numbering_node(tx):
    return (tx == 'w:numId' or tx.startswith('w:numId '))
def is_numberingstyle_node(tx):
    return (tx == 'w:numPr' or tx.startswith('w:numPr '))
def is_linebreak_node(tx):
    return (tx == 'w:br/' or tx.startswith('w:br '))
def is_insertion_node(tx):
    return (tx == 'w:ins' or tx.startswith('w:ins '))
def is_deletion_node(tx):
    return (tx == 'w:del' or tx.startswith('w:del '))
def is_deleted_text_node(tx):
    return (tx == 'w:delText' or tx.startswith('w:delText '))
def is_comment_reference_node(tx):
    return (tx == 'w:commentReference' or tx.startswith('w:commentReference '))


def need_linebreak(tx, tp):
    """
    Checks whether an additional line-break should be added
    after the given node. Single additional line-breaks are added
    after closing paragraph tags (including empty self-closing ones)
    and line-break tags.
    """
    if (tp == CLOSE or tp == OPEN and tx.endswith('/')) and is_para_node(tx):
        return True
    elif tp == OPEN and is_linebreak_node(tx):
        return True
    else:
        return False


xml_space_re = re.compile(r'xml:space="(.+?)"')


def preserve_xml_space(tx):
    """
    Sets xml:space="preserve" attribute for w:t or w:delText tags.

    When we apply_sentences_to_nodes and split some text formatting into
    several sentence formattings, we may lose leading/trailing spaces in some
    office software packages, so this function is useful when exporting docx
    (it can be also used when importing docx, but in that case we will need to
    store slightly more data in the database).
    """

    if not (is_text_node(tx) or is_deleted_text_node(tx)):
        return tx

    match_obj = xml_space_re.search(tx)
    if not match_obj:
        return tx + ' xml:space="preserve"'
    elif match_obj.group(1) == 'preserve':
        return tx
    else:
        # Get the interval [l, r), where the first group (i.e. the value of
        # the xml:space attribute) is located
        l, r = match_obj.span(1)
        return tx[:l] + 'preserve' + tx[r:]


epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)


def tokenize_xml(formatted_text):
    """
    Turns XML text into list of XML nodes.
    E.g.   <w:t>txt</w:t>  =>  [('w:t', 'o'), ('txt', 't'), ('w:t', 'c')]
    """
    tokens = formatted_text.split('>')
    nodes = []
    for token in tokens:
        if token.startswith('<'):
            # Beginning of some tag, i.e. <w:tag
            if token[1:].startswith('/'):
                nodes.append((token[2:], CLOSE))
            else:
                nodes.append((token[1:], OPEN))
        else:
            # Some text followed by <w:tag
            subtokens = token.split('<')
            # The only useful text is inside w:t or w:delText tags
            if nodes and nodes[-1][1] == OPEN:
                if is_text_node(nodes[-1][0]):
                    node_type = TEXT
                elif is_deleted_text_node(nodes[-1][0]):
                    node_type = DELETED_TEXT
                else:
                    node_type = OTHER_TEXT
                node_text = html.unescape(xml_unescape(subtokens[0]))
                nodes.append((node_text, node_type))
            if len(subtokens) > 1:
                if subtokens[1].startswith('/'):
                    nodes.append((subtokens[1][1:], CLOSE))
                else:
                    nodes.append((subtokens[1], OPEN))
    return nodes


def reconstruct_xml(nodes):
    """
    Turns list of XML nodes into XML text. Reverse of tokenize_xml().
    E.g.   [('w:t', 'o'), ('txt', 't'), ('w:t', 'c')]  =>  <w:t>txt</w:t>
    """
    reconstruction = []
    for tx, tp in nodes:
        if tp == OPEN:
            reconstruction.append('<%s>' % tx)
        elif tp == CLOSE:
            reconstruction.append('</%s>' % tx)
        elif tp in TEXT_TYPES:
            reconstruction.append(tx)
    return ''.join(reconstruction)


def process_deletions_and_insertions(nodes):
    """
    Processes deleted/inserted text in XML nodes
    (by replacing w:del/w:ins tags with DELETION/INSERTION markers,
    and also by converting w:delText tags to usual w:t tags).
    """
    enhanced_nodes = []
    for tx, tp in nodes:
        if tp == DELETED_TEXT:
            enhanced_nodes.append((tx, TEXT))
        elif is_deleted_text_node(tx):
            enhanced_nodes.append((tx.replace('w:delText', 'w:t'), tp))
        else:
            if is_deletion_node(tx):
                if tp == OPEN:
                    # Discard empty self-closing tags
                    if not tx.endswith('/'):
                        enhanced_nodes.append((OPEN, DELETION))
                else:
                    enhanced_nodes.append((CLOSE, DELETION))
            elif is_insertion_node(tx):
                if tp == OPEN:
                    # Discard empty self-closing tags
                    if not tx.endswith('/'):
                        enhanced_nodes.append((OPEN, INSERTION))
                else:
                    enhanced_nodes.append((CLOSE, INSERTION))
            else:
                enhanced_nodes.append((tx, tp))
    return enhanced_nodes


def remove_insertions(nodes):
    """
    Removes inserted text (more specifically makes it empty)
    from XML nodes, preserving all original formatting.
    Also removes auxiliary INSERTION/DELETION markers.
    """
    any_insertions = False
    nodes_without_insertions = []
    inside_insertion = False
    for tx, tp in nodes:
        if tp == TEXT and inside_insertion:
            nodes_without_insertions.append(('', TEXT))
            any_insertions = True
        else:
            if tp == INSERTION:
                if tx == OPEN:
                    inside_insertion = True
                else:
                    inside_insertion = False
            elif tp == DELETION:
                pass
            else:
                nodes_without_insertions.append((tx, tp))
    return any_insertions, nodes_without_insertions


def remove_deletions(nodes):
    """
    Removes deleted text (more specifically makes it empty)
    from XML nodes, preserving all original formatting.
    Also removes auxiliary DELETION/INSERTION markers.
    """
    any_deletions = False
    nodes_without_deletions = []
    inside_deletion = False
    for tx, tp in nodes:
        if tp == TEXT and inside_deletion:
            nodes_without_deletions.append(('', TEXT))
            any_deletions = True
        else:
            if tp == DELETION:
                if tx == OPEN:
                    inside_deletion = True
                else:
                    inside_deletion = False
            elif tp == INSERTION:
                pass
            else:
                nodes_without_deletions.append((tx, tp))
    return any_deletions, nodes_without_deletions


def apply_sentences_to_nodes(sentences, nodes):
    """
    Takes the plaintext split into sentences and the full-document list
    of nodes and returns a list of sentence-split lists of nodes.
    """
    nodesents = []
    node_idx = 0
    remain = ''
    inside_text_tag = False

    for sent in sentences:
        # Inits
        current_nodesent = []
        sent_len = len(sent)

        # If sentence ends in the middle of a TEXT node,
        # a remain is generated
        if remain:
            current_nodesent.append((remain[:sent_len], TEXT))

        # Sometimes a remain must be generated from the current remain
        if len(remain) > sent_len:
            remain = remain[sent_len:]
        else:
            # If not, eat some more nodes
            sent_len -= len(remain)
            for i in range(node_idx, len(nodes)):
                tx, tp = nodes[i]

                if tp == TEXT and inside_text_tag:
                    current_nodesent.append((tx[:sent_len], tp))
                    added_len = min(sent_len, len(tx))
                    sent_len -= added_len
                    if sent_len == 0:
                        remain = tx[added_len:]
                        break
                elif need_linebreak(tx, tp):
                    current_nodesent.append((tx, tp))
                    # This should account for 1 linebreak in the plaintext
                    if sent_len > 0:
                        sent_len -= 1
                    if sent_len == 0:
                        remain = ''
                        break
                elif tp == MARKER:
                    current_nodesent.append((tx, tp))
                else:
                    if is_text_node(tx):
                        if tp == OPEN:
                            inside_text_tag = True
                        else:
                            inside_text_tag = False
                    current_nodesent.append((tx, tp))
            node_idx = i + 1
        nodesents.append(current_nodesent)
    # Pour all the trailing nodes in the last sentence
    nodesents[-1].extend(nodes[node_idx:])
    return nodesents


def fix_runs_nodes(node_sentences):
    """
    Makes tags in each sentence consistent by closing/opening
    runs at sentence boundary.
    """
    fixed = []
    inside_deletion_or_insertion = None
    inside_run = None
    inside_text = None
    inside_runstyle = False
    run_style = []

    for sent in node_sentences:
        sent_completed = []

        # Take care of opening needed tags
        if inside_deletion_or_insertion:
            sent_completed.append((OPEN, inside_deletion_or_insertion))
            inside_deletion_or_insertion = None
        if inside_run:
            sent_completed.append((inside_run, OPEN))
            sent_completed.extend(run_style)
            inside_run = None
        if inside_text:
            sent_completed.append((inside_text, OPEN))
            inside_text = None

        sent_completed.extend(sent)

        # Track run and text tags left open
        for nd in sent_completed:
            tx, tp = nd
            if tp in (DELETION, INSERTION) and tx == OPEN:
                inside_deletion_or_insertion = tp
            elif tp in (DELETION, INSERTION) and tx == CLOSE:
                inside_deletion_or_insertion = None
            elif tp == OPEN and is_run_node(tx):
                inside_run = tx
                run_style = []
            elif tp == CLOSE and is_run_node(tx):
                inside_run = None
            elif tp == OPEN and is_text_node(tx):
                inside_text = tx
            elif tp == CLOSE and is_text_node(tx):
                inside_text = None
            elif tp == OPEN and is_runstyle_node(tx):
                run_style = [(tx, tp)]
                inside_runstyle = True
            elif tp == CLOSE and is_runstyle_node(tx):
                run_style.append((tx, tp))
                inside_runstyle = False
            elif inside_runstyle:
                run_style.append((tx, tp))

        # Now take care of closing needed tags
        if inside_text:
            sent_completed.append(('w:t', CLOSE))
        if inside_run:
            sent_completed.append(('w:r', CLOSE))
        if inside_deletion_or_insertion:
            sent_completed.append((CLOSE, inside_deletion_or_insertion))

        fixed.append(sent_completed)

    return fixed


def remove_superfluous_runs(node_sentences):
    """
    fix_runs_nodes() tends to add empty runs at the beginning of sentences
    (that begin with a run close tag). This function removes those.
    """
    clean_node_sentences = []
    for sent in node_sentences:
        # Skip if it doesn't begin with a run
        # (but don't skip if it begins with a DELETION/INSERTION marker,
        # which may surround a group of consecutive runs)
        if len(sent) < 1:
            clean_node_sentences.append(sent)
            continue
        start_from = 0
        if len(sent) >= 2 and (sent[0][1] in (DELETION, INSERTION) and sent[0][0] == OPEN):
            start_from = 1
        if not (sent[start_from][1] == OPEN and is_run_node(sent[start_from][0])):
            clean_node_sentences.append(sent)
            continue
        # Check if there's any text and decide if keep it or not
        has_text = False
        chop_from = 0
        for i, (tx, tp) in enumerate(sent):
            if tp == TEXT:
                has_text = True
                break
            elif tp == CLOSE and is_run_node(tx):
                chop_from = i + 1
                break
        if not has_text:
            clean_node_sentences.append(sent[:start_from] + sent[chop_from:])
        else:
            clean_node_sentences.append(sent)
    return clean_node_sentences


def create_numbering_counter(numfmt='none', start=1, ilvl=0):
    """
    Factory for numbering counters.
    """

    class AbstractCounter(object):
        """
        Abstract base class defining an interface for all types of counters.
        """

        def __init__(self, ilvl):
            super(AbstractCounter, self).__init__()
            self.ilvl = ilvl

        @property
        def value(self):
            raise NotImplementedError

        def increment(self):
            raise NotImplementedError

        # Useful for debugging
        def __repr__(self):
            return '<%s: %r [%d]>' % (self.__class__.__name__, self.value, self.ilvl)

    class NoneCounter(AbstractCounter):
        def __init__(self, ilvl, start):
            super(NoneCounter, self).__init__(ilvl)

        @property
        def value(self):
            return ''

        def increment(self):
            pass

    class DecimalCounter(AbstractCounter):
        def __init__(self, ilvl, start):
            super(DecimalCounter, self).__init__(ilvl)
            self._decimal = start

        @property
        def value(self):
            return str(self._decimal)

        def increment(self):
            self._decimal += 1

    class LetterCounter(AbstractCounter):
        def __init__(self, ilvl, start, lower=False):
            super(LetterCounter, self).__init__(ilvl)
            self._letter = chr(ord('A') + (start - 1) % 26)
            self._loops = (start - 1) // 26 + 1
            self._lower = lower

        @property
        def value(self):
            return (self._letter.lower() if self._lower else self._letter) * self._loops

        def increment(self):
            if self._letter == 'Z':
                self._letter = 'A'
                self._loops += 1
            else:
                self._letter = chr(ord(self._letter) + 1)

    class RomanCounter(AbstractCounter):
        NUMERALS_VALUES = [('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
                           ('C', 100), ('XC', 90), ('L', 50), ('XL', 40),
                           ('X', 10), ('IX', 9), ('V', 5), ('IV', 4),
                           ('I', 1)]

        def __init__(self, ilvl, start, lower=False):
            super(RomanCounter, self).__init__(ilvl)
            self._decimal = start
            self._lower = lower

        @property
        def value(self):
            """ Converts inner decimal integer to roman numeral within range (0, 4000). """
            roman = ''
            decimal = self._decimal
            for numeral, value in self.NUMERALS_VALUES:
                count = decimal // value
                roman += numeral * count
                decimal %= value
            return roman.lower() if self._lower else roman

        def increment(self):
            self._decimal += 1

    if numfmt == 'none':
        return NoneCounter(ilvl, start)
    elif numfmt == 'decimal':
        return DecimalCounter(ilvl, start)
    elif numfmt == 'upperLetter':
        return LetterCounter(ilvl, start)
    elif numfmt == 'lowerLetter':
        return LetterCounter(ilvl, start, lower=True)
    elif numfmt == 'upperRoman':
        return RomanCounter(ilvl, start)
    elif numfmt == 'lowerRoman':
        return RomanCounter(ilvl, start, lower=True)
    # Other counters are not implemented yet, so use dummy counter instead
    else:
        return NoneCounter(ilvl, start)


def get_formatted_numbering(lvltext, counters):
    """
    Returns a numbering string formed according to the given formatting level text
    using values from the counters.
    For example, for the level text '%1-%2-%3' and for some counters with the values
    ['III', 'B', '1'] the function will return the following numbering: 'III-B-1'.
    """
    numbering = lvltext
    for counter in counters:
        numbering = numbering.replace('%%%d' % (counter.ilvl + 1), counter.value)
    return numbering


def add_indentlevel_and_numbering_markers(nodes, numbering_styles={}):
    """
    Extends a list of XML nodes with additional nodes:
    indent-level and numbering markers.
    """
    marked_nodes = []

    inside_numberingstyle = False
    current_ilvl = last_ilvl = None
    current_numid = last_numid = None
    counters = []
    for nd in nodes:
        marked_nodes.append(nd)

        tx, tp = nd
        if is_numberingstyle_node(tx):
            if tp == OPEN:
                inside_numberingstyle = True
            else:
                inside_numberingstyle = False

        elif is_indentlevel_node(tx) and inside_numberingstyle:
            ilvl = get_val_attr(tx)
            if ilvl is not None and ilvl.isdigit():
                last_ilvl = int(ilvl)
                marked_nodes.append((INDENTLEVEL_MARKER % last_ilvl, MARKER))

        elif is_numbering_node(tx) and inside_numberingstyle:
            numid = get_val_attr(tx)
            if numid is not None and numid.isdigit():
                last_numid = int(numid)

            if last_ilvl is None or last_numid is None:
                continue

            style = numbering_styles.get(last_numid, {}).get(last_ilvl)
            if style is None:
                continue

            numfmt = style['numfmt']
            lvltext = style['lvltext']
            start = style['start']

            if last_numid != current_numid:
                current_numid = last_numid
                current_ilvl = last_ilvl
                counters = [
                    create_numbering_counter(numfmt, start, current_ilvl)
                ]
            else:
                if last_ilvl > current_ilvl:
                    current_ilvl = last_ilvl
                    counters.append(
                        create_numbering_counter(numfmt, start, current_ilvl)
                    )
                elif last_ilvl == current_ilvl:
                    if counters:
                        counters[-1].increment()
                else:
                    current_ilvl = last_ilvl
                    while counters and counters[-1].ilvl > current_ilvl:
                        counters.pop()
                    if counters and counters[-1].ilvl == current_ilvl:
                        counters[-1].increment()

            numbering = get_formatted_numbering(lvltext, counters)
            if numbering != '':
                marked_nodes.append((NUMBERING_MARKER % numbering, MARKER))

    return marked_nodes


def nodes_to_plaintext(nodes, include_markers=True):
    text = []
    for tx, tp in nodes:
        if tp == TEXT:
            text.append(tx)
        elif need_linebreak(tx, tp):
            text.append('\n')
        elif tp == MARKER and include_markers:
            text.append(tx)
    return ''.join(text)


def get_comments_from_docx(decoded_comments):
    """
    Get dict of comments in format:
    { str:comment_id: { 'author': str:author,
                        'text': str:text,
                        'timestamp': float:timestamp } }
    """

    result = {}
    parsed = BeautifulSoup(decoded_comments, features='xml')
    for comment_node in parsed.find_all('comment'):
        comment_id = comment_node['w:id']
        author = comment_node['w:author']
        text = comment_node.text
        timestamp = get_timezone_aware_timestamp(comment_node['w:date'])
        result[comment_id] = {
            'author': author,
            'text': text,
            'timestamp': timestamp
        }
    return result


def get_tz(tz_name=None):
    return pytz.timezone(tz_name) if tz_name else pytz.utc


def get_timezone_aware_datetime(date_string, default_tz_name=None):
    # If no UTC relation information is given with a time representation,
    # the time is assumed to be in local time (e.g. we treat <date>T<time>Z
    # as naive, though <date>T<time>+-hh:mm as aware)
    if date_string.endswith('Z'):
        date_string = date_string[:-1]
    dt = date_parse(date_string)
    if timezone.is_naive(dt):
        default_tz = get_tz(default_tz_name)
        dt = default_tz.localize(dt)
    return dt


def get_timezone_aware_timestamp(date_string, default_tz_name=None):
    dt = get_timezone_aware_datetime(date_string, default_tz_name)
    dt = dt.astimezone(pytz.utc)
    timestamp = (dt - epoch).total_seconds()
    # Round to whole seconds
    return int(round(timestamp))


def get_timezone_aware_datetime_from_timestamp(timestamp, tz_name=None):
    tz = get_tz(tz_name)
    # Round to whole seconds
    timestamp = int(round(timestamp))
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    dt = dt.replace(tzinfo=pytz.utc)
    dt = dt.astimezone(tz)
    return dt


def get_ordered_comments_list(fixed_node_sentences, comments):
    """
    Get list of comments where comment indices in list correspond to sentence
    indices in formatted_sentences. Sentence without comments represented by
    empty list.
    [ [], [], [(comment1, timestamp1), (comment2, timestamp2)], ... ]
    """

    comment_list = []
    trailing_comments = set()

    for node in fixed_node_sentences:
        node_comments = copy.copy(trailing_comments)
        comments_to_remove = set()

        for i in range(len(node)):
            content, tag = node[i]
            com_rng_start = comment_start_re.search(content)
            com_rng_end = comment_end_re.search(content)

            if com_rng_start:
                start_id = com_rng_start.groups()[0]
                trailing_comments.add(start_id)
                # Comment can start in current node but be not relevant
                # to text in node.

                for (content, tag) in node[i+1:]:
                    if tag == TEXT and content:
                        node_comments.add(start_id)
                        break

            elif com_rng_end:
                end_id = com_rng_end.groups()[0]
                comments_to_remove.add(end_id)

        trailing_comments = trailing_comments.difference(comments_to_remove)
        comments_for_sentence = []

        for comment_id in node_comments:
            comment = comments[comment_id]
            comments_for_sentence.append((comment['text'],
                                          comment['timestamp'],
                                          comment['author']))

        comments_for_sentence.sort(key=lambda x: x[1]) #(text, timestamp, author): timestamp

        comment_list.append(comments_for_sentence)

    return comment_list


def simplify_diff(diff):
    """
    Tries to reduce the number of changes in :diff by merging together adjacent
    removed/added parts separated with spaces and thus making :diff more
    human-readable.

    E.g., for strings 'prefix A B suffix' and 'prefix C D suffix' we get the
    following diff by default:
        = 'prefix '
        - 'A'
        + 'C'
        = ' '
        - 'B'
        + 'D'
        = ' suffix'
    Our aim here is to transform that diff into this one:
        = 'prefix '
        - 'A B'
        + 'C D'
        = ' suffix'
    """

    diff_simplified = []

    def is_equal_space(diff_entry):
        return not diff_entry.get('removed') and \
               not diff_entry.get('added') and \
               diff_entry['value'].isspace()

    i, n = 0, len(diff)
    while i < n:

        # The most interesting case implementing the main idea
        if diff[i].get('removed'):
            removed = diff[i].copy()
            if i + 1 < n and diff[i + 1].get('added'):
                added = diff[i + 1].copy()
                i += 2
            else:
                diff_simplified.append(removed)
                i += 1
                continue

            while i < n and is_equal_space(diff[i]):
                offset = 1
                removed['value'] += diff[i]['value']
                added['value'] += diff[i]['value']
                if i + 1 < n and diff[i + 1].get('removed'):
                    removed['value'] += diff[i + 1]['value']
                    offset = 2
                    if i + 2 < n and diff[i + 2].get('added'):
                        added['value'] += diff[i + 2]['value']
                        offset = 3
                i += offset

            diff_simplified.append(removed)
            diff_simplified.append(added)

        elif diff[i].get('added'):
            added = diff[i].copy()
            diff_simplified.append(added)
            i += 1

        else:
            equal = diff[i].copy()
            diff_simplified.append(equal)
            i += 1

    return diff_simplified


def remove_indentlevel_and_numbering_markers(txt):
    """ Removes auxiliary markers from text. """
    txt = numbering_re.sub('', txt)
    txt = indentlevel_re.sub('', txt)
    return txt


class CustomWordDiff(pydiff.WordDiff):

    # Consider indent-level and numbering markers as separate tokens along
    # with usual words
    _word_split_re = re.compile(
        r'(%s)' % ('|'.join([INDENTLEVEL_MARKER_RE, NUMBERING_MARKER_RE,
                             r'\s+', r'[^\w\s]+'])),
        re.UNICODE
    )

    def join(self, tokens):
        # Markers should be removed from final results
        return remove_indentlevel_and_numbering_markers(
            super(CustomWordDiff, self).join(tokens)
        )


custom_word_diff = CustomWordDiff()


def grouped_text_diff(txt_old, txt_new):
    """
    Python version of `groupedTextDiff` JavaScript function
    from 'portal/static/react/utils/groupedTextDiff.js'
    (we provide an additional Python API, since we want to make
    front-end and back-end diffs look the same).
    """

    txt_old = markers_to_linebreaks(txt_old)
    txt_new = markers_to_linebreaks(txt_new)

    diff = custom_word_diff.diff(txt_old, txt_new)
    return simplify_diff(diff)


# Internal utility functions and constants used inside `diff_change_sentence`
# (not very useful on their own)


def find_first_mismatch(p, q):
    """
    Finds positions of first differing non-space characters.
    Useful for comparing and matching strings in space-insensitive manner.
    """
    m, n = len(p), len(q)
    i = j = 0
    while i < m and j < n:
        if p[i].isspace() or q[j].isspace():
            i += p[i].isspace()
            j += q[j].isspace()
        else:
            if p[i] != q[j]:
                break
            else:
                i += 1
                j += 1
    return i, j


REMOVED = '-'
ADDED = '+'
EQUAL = '='


def get_diff_type(diff_entry):
    """ Returns string representation of diff type. """
    if diff_entry.get('removed'):
        return REMOVED
    elif diff_entry.get('added'):
        return ADDED
    else:
        return EQUAL


def split_space_prefix(p):
    """ Extracts prefix consisting of only spaces from string. """
    m = len(p)
    i = 0
    while i < m:
        if not p[i].isspace():
            break
        i += 1
    return p[:i], p[i:]


def split_space_suffix(q):
    """ Extracts suffix consisting of only spaces from string. """
    n = len(q)
    j = n - 1
    while j >= 0:
        if not q[j].isspace():
            break
        j -= 1
    j += 1
    return q[:j], q[j:]


def compose_tag(del_or_ins_tag, author, date, id):
    """ Combines (opening) w:del/w:ins tag with its main attributes. """
    return '%s%s%s%s' % (
        del_or_ins_tag,
        ' w:author="%s"' % author if author else '',
        ' w:date="%s"' % date if date else '',
        ' w:id="%s"' % id
    )


def delete_run(run, txt_idx_in_run, author, date, id):
    """ Surrounds run with w:del tags. Also replaces w:t with w:delText. """
    run[txt_idx_in_run - 1][0] = \
        run[txt_idx_in_run - 1][0].replace('w:t', 'w:delText')
    run[txt_idx_in_run + 1][0] = \
        run[txt_idx_in_run + 1][0].replace('w:t', 'w:delText')
    run[txt_idx_in_run][1] = DELETED_TEXT
    run.insert(0, [compose_tag('w:del', author, date, id), OPEN])
    run.append(['w:del', CLOSE])


def insert_run(run, author, date, id):
    """ Surrounds run with w:ins tags. """
    run.insert(0, [compose_tag('w:ins', author, date, id), OPEN])
    run.append(['w:ins', CLOSE])


def filter_run(run):
    """
    Filters run inside w:del/w:ins tags from redundant/unnecessary
    nodes (list of such nodes may be further extended).
    """
    filtered_run = []
    for (tx, tp) in run:
        if tp == OPEN and is_linebreak_node(tx):
            continue
        filtered_run.append([tx, tp])
    return filtered_run


def diff_change_sentence(txt_old, txt_new, fmt_old,
                         redlines=False, author=None, date=None, ids={}):
    """
    Compares strings :txt_old and :txt_new and applies the obtained
    plaintext diff on the nodes :fmt_old.
    Assumes that :txt_old corresponds to :fmt_old.
    If :redlines is set to True, then the text nodes will be additionally split
    into removed/added parts (i.e. w:del/w:ins tags will be added to :fmt_old
    using specified :author and :date). Each deletion/insertion inside a
    document should have a unique id, so :ids may contain some minimal starting
    values available as ids for changes within the given sentence.
    """

    diff = deque(grouped_text_diff(txt_old, txt_new))

    # Take into account that some line-breaks in the plaintext were
    # added artificially after some specific tags, so append them again
    # (temporarily) to text nodes and keep track of their counts
    txts = []
    lbrs = defaultdict(int)
    for tx, tp in fmt_old:
        if tp != TEXT:
            if need_linebreak(tx, tp):
                txts[-1] += '\n'
                lbrs[len(txts) - 1] += 1
            continue
        txts.append(tx)

    # Make sure to preserve leading/trailing whitespaces from the original
    # formatting, since `grouped_text_diff` strips input strings.
    first_non_space_txt_idx = last_non_space_txt_idx = -1
    for txt_idx, txt in enumerate(txts):
        if txt.isspace():
            continue
        if first_non_space_txt_idx == -1:
            first_non_space_txt_idx = txt_idx
        last_non_space_txt_idx = txt_idx

    any_non_space_txt = \
        first_non_space_txt_idx >= 0 and last_non_space_txt_idx >= 0

    partitions = []
    for txt_idx, txt in enumerate(txts):
        if any_non_space_txt and not \
                first_non_space_txt_idx <= txt_idx <= last_non_space_txt_idx:
            partitions.append([[EQUAL, txt]])
            continue

        prefix = suffix = ''
        if txt_idx == last_non_space_txt_idx:
            txt, suffix = split_space_suffix(txt)
        if txt_idx == first_non_space_txt_idx:
            prefix, txt = split_space_prefix(txt)

        partition = []

        while diff:
            entry = diff.popleft()
            diff_type = get_diff_type(entry)
            value = entry['value']

            if diff_type == REMOVED:
                i, j = find_first_mismatch(txt, value)
                match = value[:j]
                if match:
                    partition.append([REMOVED, match])
                txt = txt[i:]
                value = value[j:]
                # If the value wasn't matched fully, then try to match the left
                # part during the next iteration
                if value:
                    entry['value'] = value
                    diff.appendleft(entry)
                if not txt:
                    # Doesn't proceed to the next text tag, if there is a
                    # pending insertion
                    if not (diff and diff[0].get('added')):
                        break

            elif diff_type == ADDED:
                partition.append([ADDED, value])

            else:
                i, j = find_first_mismatch(txt, value)
                match = value[:j]
                if match:
                    partition.append([EQUAL, match])
                txt = txt[i:]
                value = value[j:]
                # If the value wasn't matched fully, then try to match the left
                # part during the next iteration
                if value:
                    entry['value'] = value
                    diff.appendleft(entry)
                if not txt:
                    # Doesn't proceed to the next text tag, if there is a
                    # pending insertion
                    if not (diff and diff[0].get('added')):
                        break

        if prefix:
            if partition and partition[0][0] == EQUAL:
                partition[0][1] = prefix + partition[0][1]
            else:
                partition.insert(0, [EQUAL, prefix])

        if suffix:
            if partition and partition[-1][0] == EQUAL:
                partition[-1][1] += suffix
            else:
                partition.append([EQUAL, suffix])

        partitions.append(partition)

    # Append everything remained to the last text node
    if partitions:
        for entry in diff:
            diff_type = get_diff_type(entry)
            partitions[-1].append([diff_type, entry['value']])

    # Strip appended line-breaks from the last one or
    # the last two (ADDED after REMOVED or REMOVED after EQUAL) parts
    # of the partition
    for txt_idx, partition in enumerate(partitions):
        # Handle more specific case before more general one
        if len(partition) >= 2 and (
            (partition[-1][0] == ADDED and partition[-2][0] == REMOVED) or
                (partition[-1][0] == REMOVED and partition[-2][0] == EQUAL)
        ):
            diff_value_1 = partition[-1][1]
            diff_value_2 = partition[-2][1]
            while lbrs[txt_idx]:
                if diff_value_1 and diff_value_1[-1] == '\n':
                    diff_value_1 = diff_value_1[:-1]
                if diff_value_2 and diff_value_2[-1] == '\n':
                    diff_value_2 = diff_value_2[:-1]
                lbrs[txt_idx] -= 1
            partition[-1][1] = diff_value_1
            partition[-2][1] = diff_value_2
        elif len(partition) >= 1:
            diff_value = partition[-1][1]
            while lbrs[txt_idx]:
                if diff_value and diff_value[-1] == '\n':
                    diff_value = diff_value[:-1]
                lbrs[txt_idx] -= 1
            partition[-1][1] = diff_value

    # Finally apply obtained partitions to the original formatting

    if redlines:
        fmt_new = []

        # Initialize needed keys (if they are absent) with some default values
        ids.setdefault('del', 0)
        ids.setdefault('ins', 0)

        txt_idx = -1
        run = []
        txt_idx_in_run = -1
        for (tx, tp) in fmt_old:
            if is_run_node(tx):
                if tp == OPEN:
                    run = [[tx, tp]]
                else:
                    run.append([tx, tp])

                    # If the run contains the text node, then this run should
                    # be split into several identical runs according to the
                    # corresponding partition of this text node
                    if txt_idx_in_run >= 0:
                        for part in partitions[txt_idx]:
                            if not part[1]:
                                continue
                            run_part = copy.deepcopy(run)
                            run_part[txt_idx_in_run][0] = part[1]
                            if part[0] == REMOVED:
                                delete_run(run_part, txt_idx_in_run, author,
                                           date, ids['del'])
                                run_part = filter_run(run_part)
                                ids['del'] += 1
                            elif part[0] == ADDED:
                                insert_run(run_part, author, date, ids['ins'])
                                run_part = filter_run(run_part)
                                ids['ins'] += 1
                            fmt_new.extend(run_part)
                    else:
                        fmt_new.extend(run)

                    run = []
                    txt_idx_in_run = -1

            elif run:
                run.append([tx, tp])
                if tp == TEXT:
                    txt_idx_in_run = len(run) - 1
                    txt_idx += 1

            else:
                fmt_new.append([tx, tp])

    else:
        fmt_new = copy.deepcopy(fmt_old)

        txt_idx = -1
        for idx, (tx, tp) in enumerate(fmt_old):
            if tp != TEXT:
                continue
            txt_idx += 1
            tx = ''.join(part[1] for part in partitions[txt_idx]
                         if part[0] != REMOVED)
            fmt_new[idx] = [tx, tp]

    return fmt_new


def format_comment_message(comment):
    if comment['author'] == '@beagle':
        # If the message was already set, then simply return it
        if comment['message'] is not None:
            return comment['message']

        from beagle_bot.bot import BeagleBot

        response_type = comment['response_type']
        if response_type == BeagleBot.ResponseTypes.ERROR:
            return comment['response']['title']
        else:
            response = comment['response']
            source = ''
            if response_type == BeagleBot.ResponseTypes.WIKIPEDIA:
                source = 'Wikipedia'
            elif response_type == BeagleBot.ResponseTypes.BLACKS:
                source = 'Black\'s Law Dictionary'
            if source:
                source = ' (' + source + ')'
            return u'{title}{source}\n\n{body}'.format(
                title=response['title'], source=source, body=response['body']
            )

    else:
        return comment['message']


def get_new_comments(sentences):
    """ Returns a dict with comments, added in Beagle to given sentences. """

    current_comments = [(sent.pk, sent.comments['comments'])
                        for sent in sentences if sent.comments]
    new_comments = {}
    for spk, comments in current_comments:
        for comment in comments:
            if not comment.get('is_imported', False):
                if spk not in new_comments:
                    new_comments[spk] = []
                # It is better not to change a raw comment fetched from a
                # sentence, so make a copy of it
                new_comment = comment.copy()
                message = format_comment_message(new_comment)
                if new_comment['author'] != '@beagle':
                    message = user_mention_re.sub(clean_mention, message)
                new_comment['message'] = message
                new_comments[spk].append(new_comment)
    return new_comments


def clean_mention(match):
    # Making this import global will cause errors because of circular imports
    # between core.models and richtext.xmldiff
    from core.models import CommentType

    username = match.group(1)
    if username.lower() in CommentType.DefaultMentions.BEAGLEBOT:
        return match.group(2)

    try:
        user = User.objects.get(username=username)
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        if first_name and last_name:
            clean_mention = '%s (%s %s)' % (email, first_name, last_name)
        else:
            clean_mention = '%s (%s)' % (email, username)
    except User.DoesNotExist:
        clean_mention = username

    return clean_mention


def get_comments_xml(comment_xml, new_comments, tz_name=None):
    """ Returns new word/comments.xml with new comments added. """

    parsed_comment_xml = BeautifulSoup(comment_xml, features='xml')
    _add_comment_ids(comment_xml, new_comments)

    for key in sorted(new_comments.keys()):
        com_group = new_comments[key]
        for comment in com_group:
            add_comment_to_xml(parsed_comment_xml, comment, tz_name)

    return str(parsed_comment_xml)


def _add_comment_ids(comment_xml, new_comments):
    """
    Computes and distributes comments ids.
    Does not return anything, saves all changes into given new_comments dict.
    """

    prev_comments = get_comments_from_docx(comment_xml)
    # Get min comment id to start from
    min_id = 1
    for com_id in prev_comments:
        if int(com_id) >= min_id:
            min_id = int(com_id) + 1

    # Distribute comment ids
    for spk in sorted(new_comments.keys()):
        for comment in new_comments[spk]:
            comment['id'] = str(min_id)
            min_id += 1


def add_comment_formatting(sentences, sent_com_dict):
    """
    Add comment data to sentences formatting.
    Does not return anything, saves all changes into given sentence list.
    """

    for spk in sent_com_dict:
        sent = find_first(sentences, lambda sent: sent.pk == spk)

        for comment in sent_com_dict[spk]:
            frmt = sent.formatting

            # We should begin comment range before the run in which text lies
            for i in range(len(frmt)):
                if is_run_node(frmt[i][0]):
                    last_run_node = i
                elif frmt[i][1] in (TEXT, DELETED_TEXT):
                    start_comment_ind = last_run_node
                    # Make sure to start the comment before
                    # the leading deletion/insertion
                    if start_comment_ind > 0 and \
                            (is_deletion_node(frmt[start_comment_ind - 1][0]) or
                             is_insertion_node(frmt[start_comment_ind - 1][0])):
                        start_comment_ind -= 1
                    break
            # We should end comment range after the run in which text lies
            for i in range(len(frmt)-1, -1, -1):
                if is_run_node(frmt[i][0]):
                    last_run_node = i
                elif frmt[i][1] in (TEXT, DELETED_TEXT):
                    end_comment_ind = last_run_node + 1
                    # Make sure to end the comment after
                    # the trailing deletion/insertion
                    if end_comment_ind < len(frmt) and \
                            (is_deletion_node(frmt[end_comment_ind][0]) or
                             is_insertion_node(frmt[end_comment_ind][0])):
                        end_comment_ind += 1
                    break

            com_id = comment['id']
            start_comment = [[u'w:commentRangeStart w:id="%s"/' % com_id, OPEN]]
            end_comment = [
                [u'w:commentRangeEnd w:id="%s"/' % com_id, OPEN],
                [u'w:r', OPEN],
                [u'w:commentReference w:id="%s"/' % com_id, OPEN],
                [u'w:r', CLOSE]
            ]
            changed_frmt = (
                sent.formatting[:start_comment_ind] +
                start_comment +
                sent.formatting[start_comment_ind:end_comment_ind] +
                end_comment +
                sent.formatting[end_comment_ind:]
            )
            sent.formatting = changed_frmt


def add_comments_to_doc(sent_com_dict, decoded_doc, sentences):
    """
    Add comment data into string object representing word/document.xml.
    Returns new string with changes.
    """

    parsed_doc = BeautifulSoup(decoded_doc, features='xml')

    t_tags = parsed_doc.find_all('t')
    t_tags_len = len(t_tags)
    t_iter = 0

    for sent in sentences:
        spk = sent.pk

        # Find the first and the last text tags corresponding to the sentence
        sent_len = len(markers_to_linebreaks(sent.text))
        t_tag_first = t_tags[t_iter] if t_iter < t_tags_len else None
        t_tag_last = t_tag_first
        while sent_len > 0 and t_iter < t_tags_len:
            t_tag_last = t_tags[t_iter]
            text = t_tag_last.string
            if text:
                sent_len -= len(text)
            t_iter += 1

        if spk not in sent_com_dict:
            continue

        if t_tag_first and t_tag_last:
            r_tag_first = t_tag_first.parent
            # Make sure to start the comment before
            # the leading deletion/insertion
            r_tag_first_new = r_tag_first.previous_sibling
            if r_tag_first_new and r_tag_first_new.name == 'del':
                r_tag_first = r_tag_first_new
            elif not r_tag_first_new:
                r_tag_first_new = r_tag_first.parent
                if r_tag_first_new and r_tag_first_new.name == 'ins':
                    r_tag_first = r_tag_first_new

            r_tag_last = t_tag_last.parent
            # Make sure to end the comment after
            # the trailing deletion/insertion
            r_tag_last_new = r_tag_last.next_sibling
            if r_tag_last_new and r_tag_last_new.name == 'del':
                r_tag_last = r_tag_last_new
            elif not r_tag_last_new:
                r_tag_last_new = r_tag_last.parent
                if r_tag_last_new and r_tag_last_new.name == 'ins':
                    r_tag_last = r_tag_last_new

        else:
            continue

        # Border the sentence with the appropriate comment tags
        for comment in sent_com_dict[spk]:
            com_start_tag = parsed_doc.new_tag(u'w:commentRangeStart')
            com_start_tag[u'w:id'] = comment['id']
            com_end_tag = parsed_doc.new_tag(u'w:commentRangeEnd')
            com_end_tag[u'w:id'] = comment['id']
            run_com_tag = parsed_doc.new_tag(u'w:r')
            com_ref_tag = parsed_doc.new_tag(u'w:commentReference')
            com_ref_tag[u'w:id'] = comment['id']
            run_com_tag.append(com_ref_tag)

            r_tag_first.insert_before(com_start_tag)
            r_tag_last.insert_after(com_end_tag)
            com_end_tag.insert_after(run_com_tag)

    return str(parsed_doc)


def add_comment_to_xml(parsed_comment_xml, comment, tz_name=None):
    """
    Add comment data into Beautiful Soup object representing word/comments.xml.
    Does not return anything, saves all changes into given object.
    """
    if comment['author'] == 'Beagle':  # annotation
        comment_author = 'Beagle'
    elif comment['author'] == '@beagle':  # bot's response
        comment_author = 'Beagle Bot'
    else:  # usual comment
        author = User.objects.get(username=comment['author'])
        comment_author = author.first_name
        if author.last_name:
            comment_author = '%s %s' % (comment_author, author.last_name)
        if not comment_author:
            comment_author = author.username

    dt = get_timezone_aware_datetime_from_timestamp(comment['timestamp'],
                                                    tz_name)
    comment_date = dt.isoformat()
    comment_id = comment['id']

    # Create and fill tag with comment meta information
    comment_tag = parsed_comment_xml.new_tag(u'w:comment')
    comment_tag[u'w:author'] = comment_author
    comment_tag[u'w:date'] = comment_date
    comment_tag[u'w:id'] = comment_id
    comment_tag.append(parsed_comment_xml.new_tag(u'w:p'))
    p = comment_tag.find(u'w:p')
    p.append(parsed_comment_xml.new_tag(u'w:r'))
    p_r = p.find(u'w:r')
    p_r.append(parsed_comment_xml.new_tag(u'w:t'))
    p_r.find(u'w:t').append(format_comment_message(comment))
    parsed_comment_xml.comments.append(comment_tag)


def get_basic_comments_xml():
    """ Returns base form of word/comments.xml. """

    comments_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
        'xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
        'xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">'
        '</w:comments>'
    )
    return comments_xml


def get_basic_contenttypes():
    """ Returns base form of [Content_Types].xml. """

    contenttypes = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '</Types>'
    )
    return contenttypes


def get_basic_rels():
    """ Returns base form of word/_rels/document.xml.rels. """

    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '</Relationships>'
    )
    return rels


def add_comment_relations(initial_contenttypes, initial_rels):
    """ Add info about word/comments.xml file. """

    parsed_contenttypes = BeautifulSoup(initial_contenttypes, features='xml')
    content_tag = parsed_contenttypes.new_tag(u'Override')
    content_tag[u'ContentType'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml'
    content_tag[u'PartName'] = '/word/comments.xml'
    parsed_contenttypes.Types.append(content_tag)

    parsed_rels = BeautifulSoup(initial_rels, features='xml')
    # Need to add Relationship id, so figure out minimal available
    min_id = 1
    for rel in parsed_rels.find_all('Relationship'):
        rel_id = int(rel['Id'].lstrip('rId'))
        if rel_id >= min_id:
            min_id = rel_id + 1
    rId = 'rId%s' % min_id

    rels_tag = parsed_rels.new_tag(u'Relationship')
    rels_tag[u'Id'] = rId
    rels_tag[u'Type'] = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
    rels_tag[u'Target'] = 'comments.xml'
    parsed_rels.Relationships.append(rels_tag)
    parsed_contenttypes = str(parsed_contenttypes).replace(":=", "=")
    parsed_rels = str(parsed_rels).replace(":=", "=")

    return parsed_contenttypes, parsed_rels


def get_annotations(sentences, included_annotations):
    """ Returns a dict with annotations, added in Beagle to given sentences. """

    # Use export time for timestamp of all annotations
    timestamp = time.time()

    annotations_raw = [
        (sent.id, sent.annotations['annotations'])
        for sent in sentences if sent.annotations]

    annotations_formatted = {}
    for spk, annotations in annotations_raw:
        for annotation in annotations:
            # Exclude annotations marked as False
            if not included_annotations.get(annotation['label']):
                continue
            if spk not in annotations_formatted:
                annotations_formatted[spk] = []
            annotation_formatted = format_annotation(annotation, timestamp)
            annotations_formatted[spk].append(annotation_formatted)
    for spk in annotations_formatted.keys():
        annotations_formatted[spk] = merge_multiple_annotations(
            annotations_formatted[spk]
        )
    return annotations_formatted


def format_annotation(annotation, timestamp):
    """ Extract info from annotation, useful for user. """

    # Making this import global will cause errors because of circular imports
    # between core.models and richtext.xmldiff
    from core.models import SentenceAnnotations

    message = annotation['label']
    if annotation['type'] == SentenceAnnotations.ANNOTATION_TAG_TYPE:
        # Capitalize grammar based tags
        message = message.title()

    if annotation['party']:
        message = '%s\nParty: %s' % (message, annotation['party'])

    annotation_formatted = {
        'author': 'Beagle',
        'message': message,
        'timestamp': timestamp
    }

    return annotation_formatted


def merge_multiple_annotations(annotation_group):
    """ Merge multiple annotations into one. """

    if len(annotation_group) == 1:
        return annotation_group

    annotation_group[0]['message'] = '\n\n'.join(ann['message']
                                                 for ann in annotation_group)

    return annotation_group[:1]


def add_image_relations(initial_contenttypes, initial_rels, image_name):
    """ Add info about media/image_name file. """

    image_extension = image_name.split('.')[1]
    if image_extension != 'png':
        raise NotImplementedError('Only png images are supported for now.')

    parsed_contenttypes = BeautifulSoup(initial_contenttypes, features='xml')

    # Add png contenttype if not existent
    has_png_contenttype = False
    for tag in parsed_contenttypes.find_all('Default'):
        if tag.attrs.get('ContentType') == 'image/png':
            has_png_contenttype = True

    if not has_png_contenttype:
        content_tag = parsed_contenttypes.new_tag(u'Default')
        content_tag[u'ContentType'] = 'image/png'
        content_tag[u'Extension'] = 'png'
        parsed_contenttypes.Types.append(content_tag)

    parsed_rels = BeautifulSoup(initial_rels, features='xml')
    # Need to add Relationship id, so figure out minimal available
    min_id = 1
    for rel in parsed_rels.find_all('Relationship'):
        rel_id = int(rel['Id'].lstrip('rId'))
        if rel_id >= min_id:
            min_id = rel_id + 1
    rId = 'rId%s' % min_id

    rels_tag = parsed_rels.new_tag(u'Relationship')
    rels_tag[u'Id'] = rId
    rels_tag[u'Type'] = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
    rels_tag[u'Target'] = 'media/%s' % image_name
    parsed_rels.Relationships.append(rels_tag)

    parsed_contenttypes = str(parsed_contenttypes).replace(":=", "=")
    parsed_rels = str(parsed_rels).replace(":=", "=")

    return parsed_contenttypes, parsed_rels, rId


def add_annotations_formatting(sentences, sent_ann_dict, img_rid, min_img_id):
    """
    Add annotations data to sentences formatting.
    Does not return anything, saves all changes into given sentence list.
    """

    image_id = min_img_id
    sentence_with_xmlns_tags = sentences[0]
    add_xmlns_tags_to_sentence(sentence_with_xmlns_tags)

    for spk in sent_ann_dict:
        sent = find_first(sentences, lambda sent: sent.pk == spk)

        annotation = sent_ann_dict[spk][0]
        frmt = sent.formatting

        # We put annotation comment after the run in which text lies
        # and after all existent comments.
        for i in range(len(frmt)-1, -1, -1):
            if is_run_node(frmt[i][0]):
                last_run_node = i
            elif frmt[i][1] in (TEXT, DELETED_TEXT) or \
                    is_comment_reference_node(frmt[i][0]):
                annotation_ind = last_run_node + 1
                # Make sure to skip the trailing deletion/insertion
                if annotation_ind < len(frmt) and \
                        (is_deletion_node(frmt[annotation_ind][0]) or
                         is_insertion_node(frmt[annotation_ind][0])):
                    annotation_ind += 1
                break

        ann_id = annotation['id']
        # All distances are counted in EMU. 1 pixel = 9525 EMU
        ann_nodes = [
            [u'w:commentRangeStart w:id="%s"/' % ann_id, OPEN],
            [u'w:r', OPEN],
            [u'w:rPr', OPEN],
            [u'w:vertAlign w:val="superscript"/', OPEN],
            [u'w:rPr', CLOSE],
            [u'w:drawing', OPEN],
            [u'wp:inline', OPEN],
            [u'wp:extent cx="238125" cy="161925"/', OPEN],
            [u'wp:docPr descr="Beagle annotation" id="%d" name="%s"/' % (
                image_id, ANNOTATION_IMG_NAME), OPEN],
            [u'a:graphic', OPEN],
            [u'a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"', OPEN],
            [u'pic:pic', OPEN],
            [u'pic:nvPicPr', OPEN],
            [u'pic:cNvPr descr="Beagle annotation" id="%d" name="%s"/' % (
                image_id, ANNOTATION_IMG_NAME), OPEN],
            [u'pic:cNvPicPr/', OPEN],
            [u'pic:nvPicPr', CLOSE],
            [u'pic:blipFill', OPEN],
            [u'a:blip r:embed="%s"/' % img_rid, OPEN],
            [u'a:srcRect b="0" l="0" r="0" t="0"/', OPEN],
            [u'a:stretch', OPEN],
            [u'a:fillRect/', OPEN],
            [u'a:stretch', CLOSE],
            [u'pic:blipFill', CLOSE],
            [u'pic:spPr', OPEN],
            [u'a:xfrm', OPEN],
            [u'a:off x="0" y="0"/', OPEN],
            [u'a:ext cx="238125" cy="161925"/', OPEN],
            [u'a:xfrm', CLOSE],
            [u'a:prstGeom prst="rect"/', OPEN],
            [u'a:ln/', OPEN],
            [u'pic:spPr', CLOSE],
            [u'pic:pic', CLOSE],
            [u'a:graphicData', CLOSE],
            [u'a:graphic', CLOSE],
            [u'wp:inline', CLOSE],
            [u'w:drawing', CLOSE],
            [u'w:r', CLOSE],
            [u'w:commentRangeEnd w:id="%s"/' % ann_id, OPEN],
            [u'w:r', OPEN],
            [u'w:commentReference w:id="%s"/' % ann_id, OPEN],
            [u'w:r', CLOSE]
        ]

        image_id += 1

        changed_frmt = (
            sent.formatting[:annotation_ind] +
            ann_nodes +
            sent.formatting[annotation_ind:]
        )
        sent.formatting = changed_frmt


def add_annotations_to_doc(sent_ann_dict, decoded_doc, sentences, img_rid):
    """
    Add annotation data into string object representing word/document.xml.
    Returns new string with changes.
    """

    parsed_doc = BeautifulSoup(decoded_doc, features='xml')

    t_tags = parsed_doc.find_all('t')
    t_tags_len = len(t_tags)
    t_iter = 0

    img_id = 0

    for sent in sentences:
        spk = sent.pk

        # Find the last text tag corresponding to the sentence
        sent_len = len(markers_to_linebreaks(sent.text))
        t_tag_last = None
        while sent_len > 0 and t_iter < t_tags_len:
            t_tag_last = t_tags[t_iter]
            text = t_tag_last.string
            if text:
                sent_len -= len(text)
            t_iter += 1

        if spk not in sent_ann_dict:
            continue

        if t_tag_last:
            r_tag_last = t_tag_last.parent
            # Make sure to skip the trailing deletion/insertion
            sibling = r_tag_last.next_sibling
            if sibling and sibling.name == 'del':
                r_tag_last = sibling
            elif not sibling:
                sibling = r_tag_last.parent
                if sibling and sibling.name == 'ins':
                    r_tag_last = sibling

            # If there are some comments around the sentence, then we
            # should add annotations immediately after them
            while True:
                sibling = r_tag_last.next_sibling
                if not sibling or sibling.name != 'commentRangeEnd':
                    break
                # After w:commentRangeEnd comes a run
                # containing w:commentReference
                r_tag_last = sibling.next_sibling

        else:
            continue

        # Border the sentence with the appropriate comment tags
        # (annotations are represented as comments in word/document.xml)
        for annotation in sent_ann_dict[spk]:
            r_tag = parsed_doc.new_tag(u'w:r')
            r_tag_last.insert_after(r_tag)

            com_start_tag = parsed_doc.new_tag(u'w:commentRangeStart')
            com_start_tag[u'w:id'] = annotation['id']
            com_end_tag = parsed_doc.new_tag(u'w:commentRangeEnd')
            com_end_tag[u'w:id'] = annotation['id']
            run_com_tag = parsed_doc.new_tag(u'w:r')
            com_ref_tag = parsed_doc.new_tag(u'w:commentReference')
            com_ref_tag[u'w:id'] = annotation['id']
            run_com_tag.append(com_ref_tag)

            r_tag.insert_before(com_start_tag)
            r_tag.insert_after(com_end_tag)
            com_end_tag.insert_after(run_com_tag)

            # Image tags
            rPr = parsed_doc.new_tag(u'w:rPr')
            r_tag.append(rPr)
            vertAlign = parsed_doc.new_tag(u'w:vertAlign')
            vertAlign[u'w:val'] = "superscript"
            rPr.append(vertAlign)
            drawing = parsed_doc.new_tag(u'w:drawing')
            r_tag.append(drawing)
            inline = parsed_doc.new_tag(u'wp:inline')
            drawing.append(inline)
            extent = parsed_doc.new_tag(u'wp:extent')
            extent[u'cx'] = "238125"
            extent[u'cy'] = "161925"
            inline.append(extent)
            docPr = parsed_doc.new_tag(u'wp:docPr')
            docPr[u'descr'] = "Beagle annotation"
            docPr[u'name'] = ANNOTATION_IMG_NAME
            docPr[u'id'] = str(img_id)
            inline.append(docPr)
            graphic = parsed_doc.new_tag(u'a:graphic')
            inline.append(graphic)
            graphicData = parsed_doc.new_tag(u'a:graphicData')
            graphicData[u'uri'] = \
                "http://schemas.openxmlformats.org/drawingml/2006/picture"
            graphic.append(graphicData)
            pic = parsed_doc.new_tag(u'pic:pic')
            graphicData.append(pic)
            nvPicPr = parsed_doc.new_tag(u'pic:nvPicPr')
            cNvPr = parsed_doc.new_tag(u'pic:cNvPr')
            cNvPr[u'descr'] = "Beagle annotation"
            cNvPr[u'name'] = ANNOTATION_IMG_NAME
            cNvPr[u'id'] = str(img_id)
            nvPicPr.append(cNvPr)
            cNvPicPr = parsed_doc.new_tag(u'pic:cNvPicPr')
            nvPicPr.append(cNvPicPr)
            pic.append(nvPicPr)
            blipFill = parsed_doc.new_tag(u'pic:blipFill')
            pic.append(blipFill)
            blip = parsed_doc.new_tag(u'a:blip')
            blip[u'r:embed'] = img_rid
            blipFill.append(blip)
            srcRect = parsed_doc.new_tag(u'a:srcRect')
            srcRect[u'b'] = '0'
            srcRect[u'l'] = '0'
            srcRect[u'r'] = '0'
            srcRect[u't'] = '0'
            blipFill.append(srcRect)
            stretch = parsed_doc.new_tag(u'a:stretch')
            fillRect = parsed_doc.new_tag(u'a:fillRect')
            stretch.append(fillRect)
            blipFill.append(stretch)
            spPr = parsed_doc.new_tag(u'pic:spPr')
            pic.append(spPr)
            xfrm = parsed_doc.new_tag(u'a:xfrm')
            spPr.append(xfrm)
            off = parsed_doc.new_tag(u'a:off')
            off[u'x'] = "0"
            off[u'y'] = "0"
            xfrm.append(off)
            ext = parsed_doc.new_tag(u'a:ext')
            ext[u'cx'] = "238125"
            ext[u'cy'] = "161925"
            xfrm.append(ext)
            prstGeom = parsed_doc.new_tag(u'a:prstGeom')
            prstGeom[u'prst'] = "rect"
            spPr.append(prstGeom)
            ln = parsed_doc.new_tag(u'a:ln')
            spPr.append(ln)

            r_tag_last = r_tag
            img_id += 1

    add_xmlns_tags_to_parsed_doc(parsed_doc)

    return str(parsed_doc)


def add_xmlns_tags_to_sentence(sent):
    """
    Add xmlns drawing tags to sentence formatting.
    Saves all changes into given object.
    """

    xmlns_idx = -1
    for idx, (tx, tp) in enumerate(sent.formatting):
        if tx.startswith('w:document'):
            xmlns_idx = idx
            break

    if xmlns_idx == -1:
        return

    xmlns_tags = sent.formatting[xmlns_idx][0]

    if xmlns_tags.find('xmlns:pic=') == -1:
        xmlns_tags = '%s xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"' % xmlns_tags
    if xmlns_tags.find('xmlns:a=') == -1:
        xmlns_tags = '%s xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"' % xmlns_tags
    if xmlns_tags.find('xmlns:wp=') == -1:
        xmlns_tags = '%s xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"' % xmlns_tags

    sent.formatting[xmlns_idx][0] = xmlns_tags


def add_xmlns_tags_to_parsed_doc(parsed_doc):
    """
    Add xmlns drawing tags to parsed word/document.xml.
    Saves all changes into given object.
    """

    if not parsed_doc.document.get('xmlns:pic'):
        parsed_doc.document['xmlns:pic'] = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
    if not parsed_doc.document.get('xmlns:a'):
        parsed_doc.document['xmlns:a'] = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    if not parsed_doc.document.get('xmlns:wp'):
        parsed_doc.document['xmlns:wp'] = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'


def add_xmlns_tags_to_settings(settings):
    """
    Add xmlns drawing tags to word/settings.xml and returns changed string.
    """

    parsed_settings = BeautifulSoup(settings, features='xml')
    if not parsed_settings.settings.get('xmlns:pic'):
        parsed_settings.settings['xmlns:pic'] = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
    if not parsed_settings.settings.get('xmlns:a'):
        parsed_settings.settings['xmlns:a'] = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    if not parsed_settings.settings.get('xmlns:wp'):
        parsed_settings.settings['xmlns:wp'] = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
    return str(parsed_settings)


def find_min_img_id(decoded_doc):
    """
    Finds all drawing ids in word/document.xml
    and returns minimal available id.
    """

    parsed_doc = BeautifulSoup(decoded_doc, features='xml')
    min_id = 0

    for img_props in parsed_doc.find_all('docPr'):
        img_id = int(img_props['id'])
        if img_id >= min_id:
            min_id = img_id + 1

    return min_id


def remove_doc_annotations(doc):
    parsed_doc = BeautifulSoup(doc, features='xml')
    for run in parsed_doc.find_all('r'):
        docPr = run.find('docPr')
        if docPr and docPr.get('descr') == 'Beagle annotation':
            # Remove commentRangeStart tag
            run.previous_element.decompose()
            # Remove commentRangeEnd tag
            run.next_sibling.decompose()
            # Remove commentReference tag
            run.next_sibling.decompose()
            run.decompose()
    return str(parsed_doc)


def remove_image_relations(rels):
    parsed_rels = BeautifulSoup(rels, features='xml')
    for rel in parsed_rels.find_all('Relationship'):
        if rel.get('Target') == 'media/%s' % ANNOTATION_IMG_NAME:
            rel.decompose()
            break
    return str(parsed_rels)


def remove_comments_annotations(comments):
    parsed_comments = BeautifulSoup(comments, features='xml')
    for comment in parsed_comments.find_all('comment'):
        if comment.get('w:author') == 'Beagle':
            comment.decompose()
    return str(parsed_comments)


def fix_comments_dates(comments, tz_name):
    parsed_comments = BeautifulSoup(comments, features='xml')
    for comment in parsed_comments.find_all('comment'):
        date = comment.get('w:date')
        if date:
            new_date = get_timezone_aware_datetime(date, tz_name).isoformat()
            comment['w:date'] = new_date
    return str(parsed_comments)
