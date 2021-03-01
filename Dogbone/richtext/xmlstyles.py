import numpy as np
from collections import Counter

from richtext.xmldiff import (
    OPEN, CLOSE, TEXT,
    is_para_node, is_parastyle_node, is_run_node, is_runstyle_node,
    is_text_node, is_named_parastyle_node, is_named_runstyle_node,
    is_style_size_node, is_style_bold_node, is_style_underline_node,
    get_val_attr,
)


# Default styles will get this generic label
STYLE_DEFAULTS_LABEL = '___DEFAULT___'


def parse_size_value(v):
    return int(v)


def parse_bold_value(v):
    if v is not None:
        v = v.lower()
        # Sometimes it's specified <w:b w:val="0"/>
        if v.isdigit():
            return bool(int(v))
        elif v == 'false':
            return False
        elif v == 'true':
            return True
    else:
        return True


def parse_underline_value(v):
    if v is not None:
        return v.lower() not in ['0', 'none']
    else:
        return False


def _get_sentences_styles(node_sentences, named_styles):
    """
    Used by estimate_sentences_style(). Not really usable on it's own.

    Checks styles for all the paragraphs and runs in each sentence.

    Return format:
    [([({paragraph_style}, paragraph_len), ...], [({run_style}, run_len), ...]), ...]
    """
    sentences_style = []
    p_is_open = False
    for nodes in node_sentences:
        p_styles = []  # Format ({style}, length)
        inside_p_style = False
        r_styles = []  # Format ({style}, length)
        inside_r_style = False
        inside_t = False
        curr_p_len = 0
        curr_r_style = {}
        curr_r_len = 0

        for i, nd in enumerate(nodes):
            tx, tp = nd
            if tp == OPEN and is_run_node(tx):
                curr_r_style = {}
                curr_r_len = 0
            elif tp == CLOSE and is_run_node(tx):
                r_styles.append((curr_r_style, curr_r_len))

            elif tp == OPEN and is_runstyle_node(tx) and not inside_p_style:
                curr_r_style = {}
                inside_r_style = True
            elif tp == CLOSE and is_runstyle_node(tx) and not inside_p_style:
                inside_r_style = False
            elif inside_r_style:
                if tp == CLOSE:
                    continue
                # We are only interested in OPEN nodes here
                if is_named_runstyle_node(tx):
                    named_run_style = get_val_attr(tx)
                    if named_run_style in named_styles:
                        curr_r_style.update(named_styles[named_run_style])
                elif is_style_size_node(tx):
                    curr_r_style['size'] = parse_size_value(get_val_attr(tx))
                elif is_style_bold_node(tx):
                    curr_r_style['bold'] = parse_bold_value(get_val_attr(tx))
                elif is_style_underline_node(tx):
                    curr_r_style['underline'] = parse_underline_value(get_val_attr(tx))

            elif tp == OPEN and is_para_node(tx):
                curr_p_style = {}
                curr_p_len = 0
                p_is_open = True
            elif tp == CLOSE and is_para_node(tx):
                p_styles.append((curr_p_style, curr_p_len))
                p_is_open = False

            elif tp == OPEN and is_parastyle_node(tx):
                curr_p_style = {}
                inside_p_style = True
            elif tp == CLOSE and is_parastyle_node(tx):
                inside_p_style = False
            elif inside_p_style:
                if tp == CLOSE:
                    continue
                # We are only interested in OPEN nodes here
                if is_named_parastyle_node(tx):
                    named_para_style = get_val_attr(tx)
                    if named_para_style in named_styles:
                        curr_p_style.update(named_styles[named_para_style])
                elif is_style_size_node(tx):
                    curr_p_style['size'] = parse_size_value(get_val_attr(tx))
                elif is_style_bold_node(tx):
                    curr_p_style['bold'] = parse_bold_value(get_val_attr(tx))
                elif is_style_underline_node(tx):
                    curr_p_style['underline'] = parse_underline_value(get_val_attr(tx))

            elif tp == OPEN and is_text_node(tx):
                inside_t = True
            elif tp == CLOSE and is_text_node(tx):
                inside_t = False
            elif tp == TEXT and inside_t:
                curr_r_len += len(tx)
                curr_p_len += len(tx)

        if p_is_open:
            p_styles.append((curr_p_style, curr_p_len))

        sentences_style.append((p_styles, r_styles))

    return sentences_style


def estimate_sentences_style(node_sentences, named_styles={}):
    """
    For each sentence in :node_sentences it generates a best approximation
    overall style of the sentence.
    (A sentence may contain more runs, even more paragraphs, each with
    different style.)
    A majority rule is applied for each attribute in the extracted style.
    """
    all_sent_styles = _get_sentences_styles(node_sentences, named_styles)
    sentences_style = []

    for p_styles, r_styles in all_sent_styles:
        sent_style = {}
        # Init with defaults if any
        if STYLE_DEFAULTS_LABEL in named_styles:
            sent_style = named_styles[STYLE_DEFAULTS_LABEL].copy()

        # Replace/Init with paragraph level
        if p_styles:
            p_lens = [l for s, l in p_styles]
            majority_p = p_styles[np.argmax(p_lens)][0]
            sent_style.update(majority_p)

        if not r_styles:
            sentences_style.append(sent_style)
            continue

        # -- Size --
        szs_ws = {}
        for s, l in r_styles:
            sz = sent_style.get('size', 0)
            if 'size' in s:
                sz = s['size']
            if sz > 0 and l > 0:
                if sz not in szs_ws:
                    szs_ws[sz] = 0
                szs_ws[sz] += l

        szs, ws = szs_ws.keys(), szs_ws.values()
        if np.sum(ws) > 0:
            sent_style['size'] = int(np.round(np.average(szs, weights=ws)))

        # -- Bold --
        # Check run styles and pick majority
        b_positive, b_negative = 0, 0
        for s, l in r_styles:
            if 'bold' in s and s['bold']:
                b_positive += l
            else:
                b_negative += l
        if b_positive > b_negative:
            sent_style['bold'] = True

        # -- Underline --
        # Check run styles and pick majority
        u_positive, u_negative = 0, 0
        for s, l in r_styles:
            if 'underline' in s and s['underline']:
                u_positive += l
            else:
                u_negative += l
        if u_positive > u_negative:
            sent_style['underline'] = True

        # Collect style for this sentence and move on
        sentences_style.append(sent_style)

    return sentences_style


def normalize_styles_size(sentences_style):
    """
    Gets the dominant size throughout the sentences and turns all sizes into
    relative ones (dominant +- x).
    """
    sizes = [s['size'] for s in sentences_style if 'size' in s]
    dominant = 0
    if sizes:
        dominant = Counter(sizes).most_common(1)[0][0]

    nstyles = []
    for sst in sentences_style:
        nsst = sst.copy()
        if 'size' not in nsst:
            nsst['size'] = 0
        else:
            # Limited, relative size
            nsst['size'] = max(min(nsst['size'] - dominant, 10), -8)
        nstyles.append(nsst)
    return nstyles
