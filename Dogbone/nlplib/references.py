import re
from nltk import RegexpParser
from nlplib.grammars import EXTERNAL_REFERENCES_GRAMMAR, REFERENCES_TYPES
from nlplib.utils import extract_nodes, tree2str, TLDS, postprocess_text


# URL_RE = re.compile(r'((http|ftp|https)://[a-zA-Z][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,5}[^\s\)\(:]*)')
URL_RE = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}\.|[a-z0-9.\-]+\.[a-z]{2,6}/)(?:[^\s()<>]+|\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))\b')
EMAIL_RE = re.compile(r'([a-z0-9_\-\.]+@[a-z0-9_\-\.]+\.[a-z]{2,3})', re.IGNORECASE)
DOMAIN_RE = re.compile(r'\b([a-z0-9\-\.]+\.(?:' + '|'.join(TLDS) + '))\b', re.IGNORECASE)


references_parser = RegexpParser(EXTERNAL_REFERENCES_GRAMMAR)


def parse_references(wt_text):
    """ Apply the mention grammar on a wordtagged sentence """
    return references_parser.parse(wt_text)


class Reference:
    TYPE_URL = (0, 'URL')
    TYPE_STANDARD = (1, 'Standard')
    TYPE_EMAIL = (2, 'Email')
    TYPE_DOMAIN = (3, 'Domain')
    TYPE_COMMON_REFERENCE = (3, 'Reference')
    TYPE_OTHER = (100, 'Other')

    ALL_TYPES = [TYPE_URL, TYPE_DOMAIN, TYPE_COMMON_REFERENCE, TYPE_EMAIL, TYPE_OTHER, TYPE_OTHER, TYPE_STANDARD]

    def __init__(self, form, reftype, pos_start, sent_idx):
        self.form = form
        self.reftype = reftype
        self.pos_start = pos_start
        self.sent_idx = sent_idx

    @staticmethod
    def label2type(label):
        if label.lower() == 'url':
            return Reference.TYPE_URL

        if label.lower() == 'domain':
            return Reference.TYPE_DOMAIN

        if label.lower() == 'standard':
            return Reference.TYPE_STANDARD

        if label.lower() in ['reference', 'common_reference']:
            return Reference.TYPE_COMMON_REFERENCE

        if label.lower() in ['email', 'e-mail', 'mail']:
            return Reference.TYPE_EMAIL

        if label.lower() == 'other':
            return Reference.TYPE_OTHER

        return None

    def __hash__(self):
        return hash((self.form, self.reftype))

    def __eq__(self, other):
        try:
            return self.form == other.form and self.reftype == other.reftype
        except:
            return False

    def __str__(self):
        return '[%s] %s (s:%d)' % (self.reftype[1], self.form, self.pos_start)

    def __repr__(self):
        return '<[%s]%s>' % (self.reftype[1], self.form)


class ExternalReferencesAnalyzer:
    def __init__(self, rawtext, sentences, wordtagged=None, parties=None):
        self._wordtagged = wordtagged
        self._sentences = sentences
        self._text = rawtext
        self._parsed_sentences = None
        self._references = None
        self._parties = [p.lower() for p in parties]

    @property
    def text(self):
        return self._text

    @property
    def wordtagged(self):
        return self._wordtagged

    @property
    def parsed_sentences(self):
        if self._parsed_sentences is None:
            self._parse_sentences()

        return self._parsed_sentences

    @property
    def references(self):
        if self._references is None:
            self._references = []

        return self._references

    def _get_urls(self):
        for i, s in enumerate(self._sentences):
            # Create a copy of the text
            text_copy = s[:]

            matches = list(URL_RE.finditer(text_copy))
            for m in matches:
                self.references.append(Reference(m.group(), Reference.TYPE_URL, m.start(), i))

            # Remove the matched items
            for m in matches:
                text_copy = text_copy[:m.start()] + ' ' * len(m.group()) + text_copy[m.end():]

            matches = list(EMAIL_RE.finditer(text_copy))
            for m in matches:
                self.references.append(Reference(m.group(), Reference.TYPE_EMAIL, m.start(), i))

            # Remove the matched items
            for m in matches:
                text_copy = text_copy[:m.start()] + ' ' * len(m.group()) + text_copy[m.end():]

            matches = list(DOMAIN_RE.finditer(text_copy))
            for m in matches:
                if not (m.group().lower().startswith('www.') and len(m.group()) <= 7):
                    self.references.append(Reference(m.group(), Reference.TYPE_DOMAIN, m.start(), i))

    def _parse_sentences(self):
        self._parsed_sentences = [parse_references(ss) for ss in self.wordtagged]

    def _get_standards(self):
        standards = []

        for i, ps in enumerate(self.parsed_sentences):
            for t in extract_nodes(ps, predicate=lambda x: x.label() in REFERENCES_TYPES):
                standtxt = postprocess_text(tree2str(t))
                offset = self._sentences[i].find(standtxt)
                standards.append(Reference(standtxt, Reference.label2type(t.label()), offset, i))
        self.references.extend(standards)

    def analyze(self):
        self.references = []
        self._get_urls()
        self._get_standards()

        self.references = [r for r in self.references
                           if r.form.lower() not in self._parties]
        return set(self.references)
