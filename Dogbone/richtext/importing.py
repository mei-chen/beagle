import os
import requests
import tempfile
import re
import urllib
import zipfile

from bs4 import BeautifulSoup
from richtext.xmldiff import (
    DOCX_DOCUMENT_FNAME, DOCX_STYLES_FNAME, DOCX_NUMBERING_FNAME,
    ANNOTATION_IMG_NAME, DOCX_RELS_FNAME, DOCX_COMMENTS_FNAME,
    nodes_to_plaintext, tokenize_xml, apply_sentences_to_nodes,
    fix_runs_nodes, remove_superfluous_runs,
    get_comments_from_docx, get_ordered_comments_list,
    add_indentlevel_and_numbering_markers,
    process_deletions_and_insertions, remove_insertions, remove_deletions,
    remove_image_relations, remove_doc_annotations, remove_comments_annotations,
    fix_comments_dates
)
from richtext.xmlstyles import (
    parse_size_value, parse_bold_value, parse_underline_value,
    estimate_sentences_style, normalize_styles_size, STYLE_DEFAULTS_LABEL
)
from StringIO import StringIO
import utils.conversion
from utils.conversion import filedecode, contentsdecode
from nlplib.utils import split_sentences

page_rgx = re.compile(r'^[Pp]age \d+\s*$')


class DOCTypeException(Exception):
    pass


def get_named_styles_from_docx(filename):
    """
    Parses the styles.xml file for named styles in a docx document.
    """
    styles = {}

    def extract_style_from_node(n):
        style = {}
        # Size
        sz = n.find('w:sz')
        if sz:
            style['size'] = parse_size_value(sz['w:val'])
        # Bold
        b = n.find('w:b')
        if b:
            style['bold'] = parse_bold_value(b.get('w:val'))
        # Underline
        u = n.find('w:u')
        if u:
            style['underline'] = parse_underline_value(u.get('w:val'))
        return style

    with zipfile.ZipFile(filename, mode='r') as zin:
        if DOCX_STYLES_FNAME not in zin.namelist():
            return {}

        stylestext = zin.read(DOCX_STYLES_FNAME)
        parsed = BeautifulSoup(stylestext)
        xmlstyles = parsed.find_all('w:style')

        for s in xmlstyles:
            styles[s['w:styleid']] = extract_style_from_node(s)

        # Read document defaults
        defaults = parsed.find('w:docdefaults')
        if defaults:
            styles[STYLE_DEFAULTS_LABEL] = extract_style_from_node(defaults)

    return styles


def get_numbering_styles_from_docx(filename):
    """
    Parses the numbering.xml file for numbering styles in a docx document.
    """

    def extract_indentlevel_styles(abstractnum):
        styles = {}

        lvls = abstractnum.find_all('w:lvl')
        for lvl in lvls:
            style = {}
            ilvl = int(lvl['w:ilvl'])

            numfmt = lvl.find('w:numfmt')
            if numfmt:
                style['numfmt'] = numfmt.get('w:val', 'none')
            else:
                style['numfmt'] = 'none'

            islgl = lvl.find('w:islgl')
            if islgl:
                style['numfmt'] = 'decimal'

            lvltext = lvl.find('w:lvltext')
            if lvltext:
                style['lvltext'] = lvltext.get('w:val', '')
            else:
                style['lvltext'] = ''

            start = lvl.find('w:start')
            if start:
                style['start'] = int(start.get('w:val', '1'))
            else:
                style['start'] = 1

            styles[ilvl] = style

        return styles

    with zipfile.ZipFile(filename, mode='r') as zin:
        try:
            content = zin.read(DOCX_NUMBERING_FNAME)
            soup = BeautifulSoup(content)
        except KeyError:
            return {}

    numbering = {}

    nums = soup.find_all('w:num')
    for num in nums:
        numid = int(num['w:numid'])
        abstractnumid = num.find('w:abstractnumid')['w:val']
        abstractnum = soup.find('w:abstractnum',
                                attrs={'w:abstractnumid': abstractnumid})
        # Check whether abstractnum contains any actual properties or
        # simply refers to another abstractnum
        numstylelink = abstractnum.find('w:numstylelink')
        if numstylelink:
            val = numstylelink['w:val']
            stylelink = soup.find('w:stylelink', attrs={'w:val': val})
            if stylelink:
               abstractnum = stylelink.parent
        numbering[numid] = extract_indentlevel_styles(abstractnum)

    return numbering


def parse_docx(filename):
    """
    The whole docx processing workflow.
    Takes in the filename and spits out the sentence split plain text,
    the sentence split XML nodes and the extracted styles for each sentence.
    """
    # Read
    with zipfile.ZipFile(filename, mode='r') as zin:
        doctext = zin.read(DOCX_DOCUMENT_FNAME)
        dec_contents = contentsdecode(doctext)

        # Get comments from docx if exist
        if DOCX_COMMENTS_FNAME in zin.namelist():
            doc_comments = zin.read(DOCX_COMMENTS_FNAME)
            decoded_comments = contentsdecode(doc_comments)
            comments = get_comments_from_docx(decoded_comments)
        else:
            comments = None

    # Get named styles from docx
    named_styles = get_named_styles_from_docx(filename)

    # Get numbering styles from docx
    numbering_styles = get_numbering_styles_from_docx(filename)

    # -- Parse --
    # Generate the nodes format
    nodes = tokenize_xml(dec_contents)
    nodes = add_indentlevel_and_numbering_markers(nodes, numbering_styles)
    nodes = process_deletions_and_insertions(nodes)

    # Get (space preserving) plaintext (no markers, for a better sentence split)
    plaintext = nodes_to_plaintext(nodes, include_markers=False)

    # Split the plaintext into sentences
    txtsentences = split_sentences(plaintext)

    # Construct nodes format split into sentences (from sentence split plaintext and raw nodes format)
    node_sentences = apply_sentences_to_nodes(txtsentences, nodes)

    # Close/open runs at sentence boundary
    fixed_node_sentences = remove_superfluous_runs(fix_runs_nodes(node_sentences))

    # Estimate a rough style for each sentence based on pPr, rPr and styles.xml
    sentence_styles = estimate_sentences_style(fixed_node_sentences, named_styles)

    # Fill in size to styles that are still missing
    # Normalize all sizes around the average size in doc
    normalized_sentence_styles = normalize_styles_size(sentence_styles)

    # Regenerate plaintext sentences with markers included this time
    txtsentences = map(nodes_to_plaintext, node_sentences)

    # Get commented sentences with comment ids
    if comments:
        sentences_comments = get_ordered_comments_list(fixed_node_sentences,
                                                       comments)
    else:
        sentences_comments = None

    # Check whether there are changed sentences which have to be approved,
    # and cut off unapproved changes from the initial plaintext and formatting
    sentences_changes = []
    for i in range(len(txtsentences)):
        any_insertions, fixed_node_sentence_before = remove_insertions(fixed_node_sentences[i])
        any_deletions, fixed_node_sentence_after = remove_deletions(fixed_node_sentences[i])
        if any_insertions or any_deletions:
            txtsentence_before = nodes_to_plaintext(fixed_node_sentence_before)
            txtsentence_after = nodes_to_plaintext(fixed_node_sentence_after)
            fixed_node_sentences[i] = fixed_node_sentence_before
            txtsentences[i] = txtsentence_before
            sentences_changes.append(txtsentence_after)
        else:
            sentences_changes.append(None)

    return (txtsentences, fixed_node_sentences, normalized_sentence_styles,
            sentences_comments, sentences_changes)


def source_handler(source):
    """ Factory for uploaders """

    class LocalUploader:
        def process(self, uploaded_file=None, file_url=None, file_name=None, access_token=None):
            if not uploaded_file:
                msg = 'Error: Received an upload request without attachment or URL'
                return False, msg

            original_filename = uploaded_file.name

            temp_file_handle = tempfile.TemporaryFile()
            temp_file_handle.write(uploaded_file.read())
            temp_file_handle.seek(0)
            return True, (original_filename, temp_file_handle)

    class URLUploader:
        def process(self, uploaded_file=None, file_url=None, file_name=None, access_token=None):
            if not file_url:
                msg = 'Error: source is URL but file url not supplied'
                return False, msg

            filename, extension = os.path.splitext(file_url)
            filename = filename[filename.rfind('/')+1:]
            filename = urllib.unquote(filename).decode('utf8')
            original_filename = "%s%s" % (filename, extension)

            temp_file_handle = tempfile.TemporaryFile()
            response = requests.get(file_url, stream=True)
            if not response.ok:
                return False, 'Bad stream'

            for block in response.iter_content(1024):
                if not block:
                    break
                temp_file_handle.write(block)
            temp_file_handle.seek(0)
            return True, (original_filename, temp_file_handle)

    class GDriveUploader:
        def process(self, uploaded_file=None, file_url=None, file_name=None, access_token=None):
            original_filename = file_name

            if not access_token:
                return False, 'Bad access token'

            temp_file_handle = tempfile.TemporaryFile()
            headers = {'stream': True, 'Authorization': 'Bearer ' + access_token}
            response = requests.get(file_url, headers=headers)

            if not response.ok:
                return False, 'Bad file URL, or Authorization problem'

            for block in response.iter_content(1024):
                if not block:
                    break
                temp_file_handle.write(block)
            temp_file_handle.seek(0)
            return True, (original_filename, temp_file_handle)

    class InvalidUploader:
        def process(self, uploaded_file=None, file_url=None, file_name=None, access_token=None):
            msg = 'Error: Invalid file upload source'
            return False, msg

    if source == 'local':
        return LocalUploader()
    elif source == 'url':
        return URLUploader()
    elif source == 'dropbox':
        return URLUploader()
    elif source == 'gdrive':
        return GDriveUploader()
    else:
        return InvalidUploader()


def conversion_handler(file_extension):
    """
    Factory for file converters.
    The payload returned by the process() method has the format:
      (plaintext_sentence_list, nodes_sentence_list, sentence_style_list)
    """

    class TxtConverter:
        def process(self, document, filename):
            plaintext = filedecode(filename)
            # Tokenize paragraphs and sentences
            plainsentences = split_sentences(plaintext)
            sentences_tuple = (plainsentences, None, None)
            return True, sentences_tuple

    class XmlConverter:
        def process(self, document, filename):
            parsed = BeautifulSoup(contentsdecode(open(filename).read()), 'lxml')
            html_parsed = BeautifulSoup(parsed.text.encode('utf-8'), 'lxml')

            content = html_parsed.text.replace(u'\xa0', ' ')
            lines = []

            for line in content.splitlines():
                if not page_rgx.match(line):
                    lines.append(line)
            plaintext = '\n'.join(lines)

            # Tokenize paragraphs and sentences
            plainsentences = split_sentences(plaintext)
            sentences_tuple = (plainsentences, None, None)
            return True, sentences_tuple

    class DocXConverter:
        def process(self, document, filename):
            new_file = None
            with zipfile.ZipFile(filename, mode='r') as zin:
                if 'word/media/%s' % ANNOTATION_IMG_NAME in zin.namelist():
                    # Remove previously exported annotations
                    new_file = remove_annotations(zin)

            if new_file:
                with open(filename, 'w') as write_file:
                    write_file.write(new_file.getvalue())
                    new_file.close()

            new_file = None
            if document.time_zone:
                # Make all internal dates time zone aware
                with zipfile.ZipFile(filename, mode='r') as zin:
                    # Dates problem only occur in word/comments.xml
                    if DOCX_COMMENTS_FNAME in zin.namelist():
                        tz_name = document.time_zone
                        new_file = fix_dates(zin, tz_name)

            if new_file:
                with open(filename, 'w') as write_file:
                    write_file.write(new_file.getvalue())
                    new_file.close()

            with open(filename, 'rb') as read_file:
                document.save_docx(read_file)
            sentences_tuple = parse_docx(filename)
            return True, sentences_tuple

    class DocConverter:
        def process(self, document, filename):
            tempfilename = filename + '.doc'

            with open(filename, 'rb') as read_file:
                with open(tempfilename, 'w+') as doc_tempfile:
                    doc_tempfile.write(read_file.read())
                read_file.seek(0)
                document.save_doc(read_file)

            # First convert to a docx file
            docxfile = utils.conversion.doc_to_docx(tempfilename)
            success, sentences_tuple = DocXConverter().process(document, docxfile)

            return True, sentences_tuple

    class PDFConverter:
        def process(self, document, filename):
            tempfilename = filename + '.pdf'

            with open(filename, 'rb') as read_file:
                with open(tempfilename, 'w+') as pdf_tempfile:
                    pdf_tempfile.write(read_file.read())
                read_file.seek(0)
                document.save_pdf(read_file)

            # First convert to a docx file
            docxfile = utils.conversion.pdf_to_docx(tempfilename)
            converter_class = DocXConverter
            if docxfile.endswith('.txt'):
                # External APIs for converting pdf to docx were not available,
                # so we simply converted to txt using our available tools
                converter_class = TxtConverter
            success, sentences_tuple = converter_class().process(document, docxfile)

            return True, sentences_tuple

    class InvalidConverter:
        def process(self, document, filename):
            msg = 'Document type not supported'
            return False, msg

    lwextension = file_extension.lower()

    if lwextension == '.txt':
        return TxtConverter()
    elif lwextension == '.pdf':
        return PDFConverter()
    elif lwextension == '.docx':
        return DocXConverter()
    elif lwextension == '.doc':
        return DocConverter()
    elif lwextension == '.xml':
        return XmlConverter()
    else:
        return InvalidConverter()


def remove_annotations(zin):
    rels = contentsdecode(zin.read(DOCX_RELS_FNAME))
    doc = contentsdecode(zin.read(DOCX_DOCUMENT_FNAME))
    coms = contentsdecode(zin.read(DOCX_COMMENTS_FNAME))

    new_doc = remove_doc_annotations(doc).encode('utf-8')
    new_rels = remove_image_relations(rels).encode('utf-8')
    new_comments = remove_comments_annotations(coms).encode('utf-8')
    new_file = StringIO()

    with zipfile.ZipFile(new_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == DOCX_DOCUMENT_FNAME:
                zout.writestr(DOCX_DOCUMENT_FNAME, new_doc)
            elif item.filename == DOCX_RELS_FNAME:
                zout.writestr(DOCX_RELS_FNAME, new_rels)
            elif item.filename == DOCX_COMMENTS_FNAME:
                zout.writestr(DOCX_COMMENTS_FNAME, new_comments)
            elif item.filename == 'word/media/%s' % ANNOTATION_IMG_NAME:
                continue
            else:
                zout.writestr(item, zin.read(item.filename))

    new_file.seek(0)

    return new_file


def fix_dates(zin, tz_name):
    comments = contentsdecode(zin.read(DOCX_COMMENTS_FNAME))

    new_comments = fix_comments_dates(comments, tz_name).encode('utf-8')

    new_file = StringIO()

    with zipfile.ZipFile(new_file, mode='w',
                         compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == DOCX_COMMENTS_FNAME:
                zout.writestr(DOCX_COMMENTS_FNAME, new_comments)
            else:
                zout.writestr(item, zin.read(item.filename))

    new_file.seek(0)

    return new_file
