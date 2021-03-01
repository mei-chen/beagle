import docx
import os
import zipfile
from StringIO import StringIO
from xml.sax.saxutils import escape as xmlescape

from bs4 import BeautifulSoup
from nlplib.utils import markers_to_linebreaks
from django.conf import settings

from integrations.s3 import get_s3_bucket_manager
from richtext.xmldiff import (
    DOCX_DOCUMENT_FNAME, DOCX_COMMENTS_FNAME,
    DOCX_CONTENTTYPES_FNAME, DOCX_RELS_FNAME,
    DOCX_SETTINGS_FNAME, ANNOTATION_IMG_NAME,
    TEXT_TYPES, OPEN,
    preserve_xml_space,
    reconstruct_xml,
    get_tz,
    grouped_text_diff, diff_change_sentence,
    get_new_comments, get_comments_xml, add_comment_relations,
    add_comments_to_doc, add_comment_formatting,
    get_basic_comments_xml, get_basic_contenttypes, get_basic_rels,
    get_annotations, add_annotations_formatting, add_annotations_to_doc,
    add_image_relations, add_xmlns_tags_to_settings, find_min_img_id
)
from utils.conversion import contentsdecode


ANNOTATION_IMG_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                   'resources', ANNOTATION_IMG_NAME)


def document_to_docx(document, s3_path,
                     include_comments=False,
                     include_track_changes=False,
                     included_annotations=None):
    """ Produces a plaintext docx from the :document Document model. """

    # Create an empty document using some default templates
    xdoc = docx.Document()

    initial_temporary_archive = StringIO()

    # Save the document as an initial archive
    xdoc.save(initial_temporary_archive)

    initial_temporary_archive.seek(0)

    new_temporary_archive = StringIO()

    # Create a new archive by copying the initial archive,
    # but without document.xml; also read initial document.xml.
    with zipfile.ZipFile(initial_temporary_archive, mode='r') as zin, \
            zipfile.ZipFile(new_temporary_archive, mode='w') as zout:
        zout.comment = zin.comment  # Preserve the comment
        for item in zin.infolist():
            if item.filename != DOCX_DOCUMENT_FNAME:
                zout.writestr(item, zin.read(item.filename))
        initial_doc = contentsdecode(zin.read(DOCX_DOCUMENT_FNAME))

    tz_name = document.time_zone

    # Reconstruct the document
    sentences = document.get_sorted_sentences()
    new_doc = reconstruct_docx(initial_doc, sentences, include_track_changes,
                               tz_name)

    # Write new document.xml to the new archive
    with zipfile.ZipFile(new_temporary_archive, mode='a',
                         compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(DOCX_DOCUMENT_FNAME, new_doc.encode('utf-8'))

    new_temporary_archive.seek(0)

    result_docx = new_temporary_archive

    # Add comments
    if include_comments:
        result_docx = add_comments_to_docx(result_docx, sentences,
                                           from_plain=True, tz_name=tz_name)

    # Add annotations
    if included_annotations:
        result_docx = add_annotations_to_docx(result_docx, sentences,
                                              included_annotations,
                                              from_plain=True, tz_name=tz_name)

    # Save the in-memory file to the specified path in S3
    s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
    s3_bucket.save_file(s3_path, result_docx)


def reconstruct_docx(initial_doc, sentences, redlines=True, tz_name=None):
    soup = BeautifulSoup(initial_doc, features='xml')

    sectPr_tag = soup.body.sectPr
    p_tag = soup.new_tag(u'w:p')

    del_id = 0
    ins_id = 0

    for sentence_index, sentence in enumerate(sentences):
        if redlines and not sentence.accepted:
            latest_approved_revision = sentence.latest_approved_revision
            if latest_approved_revision:
                diff = grouped_text_diff(latest_approved_revision.text,
                                         sentence.text)
            else:
                diff = [{u'value': markers_to_linebreaks(sentence.text)}]
        else:
            diff = [{u'value': markers_to_linebreaks(sentence.text)}]

        # Add a single whitespace after each sentence, which aren't located
        # at the end of the current paragraph or at the end of the document
        if not sentence.newlines and sentence_index != len(sentences) - 1:
            last_entry = diff[-1]
            if not (last_entry.get(u'removed') or last_entry.get(u'added')):
                last_entry[u'value'] += u' '
            else:
                diff.append({u'value': u' '})
            sentence.text += u' '

        for entry in diff:
            text = entry[u'value']

            if entry.get(u'removed'):
                del_tag = soup.new_tag(u'w:del')
                del_tag[u'w:id'] = str(del_id)
                del_id += 1
                del_tag[u'w:author'] = get_modifier_name(sentence)
                del_tag[u'w:date'] = get_creation_time(sentence, tz_name)

                r_tag = soup.new_tag(u'w:r')
                delText_tag = soup.new_tag(u'w:delText')
                delText_tag[u'xml:space'] = u'preserve'
                delText_tag.append(text)
                r_tag.append(delText_tag)
                del_tag.append(r_tag)
                p_tag.append(del_tag)

            elif entry.get(u'added'):
                ins_tag = soup.new_tag(u'w:ins')
                ins_tag[u'w:id'] = str(ins_id)
                ins_id += 1
                ins_tag[u'w:author'] = get_modifier_name(sentence)
                ins_tag[u'w:date'] = get_creation_time(sentence, tz_name)

                r_tag = soup.new_tag(u'w:r')
                t_tag = soup.new_tag(u'w:t')
                t_tag[u'xml:space'] = u'preserve'
                t_tag.append(text)
                r_tag.append(t_tag)
                ins_tag.append(r_tag)
                p_tag.append(ins_tag)

            else:
                r_tag = soup.new_tag(u'w:r')
                t_tag = soup.new_tag(u'w:t')
                t_tag[u'xml:space'] = u'preserve'
                t_tag.append(text)
                r_tag.append(t_tag)
                p_tag.append(r_tag)

        for _ in range(sentence.newlines):
            sectPr_tag.insert_before(p_tag)
            p_tag = soup.new_tag(u'w:p')

    if p_tag.contents:
        sectPr_tag.insert_before(p_tag)

    # Add a final page-break
    p_tag = soup.new_tag(u'w:p')
    r_tag = soup.new_tag(u'w:r')
    br_tag = soup.new_tag(u'w:br')
    br_tag[u'w:type'] = u'page'
    r_tag.append(br_tag)
    p_tag.append(r_tag)
    sectPr_tag.insert_before(p_tag)

    return unicode(soup)


def get_modifier_name(sentence):
    modifier = sentence.modified_by
    modifier_full_name = []
    if modifier.first_name:
        modifier_full_name.append(modifier.first_name)
    if modifier.last_name:
        modifier_full_name.append(modifier.last_name)
    modifier_full_name = ' '.join(modifier_full_name)
    return modifier_full_name or modifier.username


def get_creation_time(sentence, tz_name=None):
    tz = get_tz(tz_name)
    # Django stores aware datetimes in the db (since USE_TZ = True),
    # so we can freely convert between time zones
    dt = sentence.created.astimezone(tz)
    # Round to seconds by discarding microseconds
    dt = dt.replace(microsecond=0)
    return dt.isoformat()


def document_to_rich_docx(document, s3_path,
                          include_comments=False,
                          include_track_changes=False,
                          included_annotations=None):
    """ Produces a richtext docx from the :document Document model. """

    docx_file = document.get_docx()

    if not docx_file:
        # Fallback on the un-formatted docx
        document_to_docx(
            document,
            s3_path,
            include_comments=include_comments,
            include_track_changes=include_track_changes,
            included_annotations=included_annotations
        )
        return

    temporary_archive = StringIO()

    # Create a temporary copy of the archive without document.xml
    with zipfile.ZipFile(docx_file, mode='r') as zin, \
            zipfile.ZipFile(temporary_archive, mode='w') as zout:
        zout.comment = zin.comment  # Preserve the comment
        for item in zin.infolist():
            if item.filename != DOCX_DOCUMENT_FNAME:
                zout.writestr(item, zin.read(item.filename))

    tz_name = document.time_zone

    # Reconstruct the document
    sentences = document.get_sorted_sentences()
    doc = reconstruct_rich_docx(sentences, include_track_changes, tz_name)

    # Now add document.xml with its new data
    with zipfile.ZipFile(temporary_archive, mode='a',
                         compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(DOCX_DOCUMENT_FNAME, doc.encode('utf-8'))

    temporary_archive.seek(0)

    result_docx = temporary_archive

    # Add comments
    if include_comments:
        result_docx = add_comments_to_docx(result_docx, sentences,
                                           tz_name=tz_name)

    # Add annotations
    if included_annotations:
        result_docx = add_annotations_to_docx(result_docx, sentences, included_annotations,
                                              tz_name=tz_name)

    # Save the in-memory file to the specified path in S3
    s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
    s3_bucket.save_file(s3_path, result_docx)


def reconstruct_rich_docx(sentences, redlines=True, tz_name=None):
    nodes = []
    ids = {}
    for sentence in sentences:
        if redlines and not sentence.accepted:
            latest_approved_revision = sentence.latest_approved_revision
            if latest_approved_revision:
                sentence_text = sentence.text if not sentence.deleted else ''
                sentence.formatting = \
                    diff_change_sentence(latest_approved_revision.text,
                                         sentence_text,
                                         latest_approved_revision.formatting,
                                         redlines=True,
                                         author=get_modifier_name(sentence),
                                         date=get_creation_time(sentence,
                                                                tz_name),
                                         ids=ids)
        nodes.extend(sentence.formatting)
    # Escape special characters in text nodes
    nodes = [(xmlescape(n), t)
             if t in TEXT_TYPES else
             (preserve_xml_space(n) if t == OPEN else n, t)
             for n, t in nodes]
    doc = reconstruct_xml(nodes)
    return doc


def add_comments_to_docx(temp_docx, sentences, from_plain=False, tz_name=None):
    """
    Check if there are new comments added to document's sentences
    and get them if yes.
    """

    comments_to_add = get_new_comments(sentences)

    if not comments_to_add:
        return temp_docx

    initial_comments = None
    initial_contenttypes = None
    initial_rels = None
    result_docx = StringIO()

    with zipfile.ZipFile(temp_docx, mode='r') as zin:
        for name in zin.namelist():
            if name == DOCX_COMMENTS_FNAME:
                initial_comments = contentsdecode(zin.read(name))
            elif name == DOCX_CONTENTTYPES_FNAME:
                initial_contenttypes = contentsdecode(zin.read(name))
            elif name == DOCX_RELS_FNAME:
                initial_rels = contentsdecode(zin.read(name))
            elif name == DOCX_DOCUMENT_FNAME:
                initial_doc = contentsdecode(zin.read(name))

    if not initial_comments:
        # There are no comment file in initial document, so we need
        # to initialize it and also add relations and content type
        initial_comments = get_basic_comments_xml()
        if not initial_contenttypes:
            initial_contenttypes = get_basic_contenttypes()
        if not initial_rels:
            initial_rels = get_basic_rels()
        new_contenttypes, new_rels = add_comment_relations(
            initial_contenttypes, initial_rels)
    else:
        # We can use existing relations
        new_contenttypes, new_rels = initial_contenttypes, initial_rels

    new_comments = get_comments_xml(initial_comments, comments_to_add, tz_name)

    if from_plain:
        new_doc = add_comments_to_doc(comments_to_add, initial_doc, sentences)
    else:
        add_comment_formatting(sentences, comments_to_add)
        # Redlines were already added, and there is no need to compute diffs
        # and restore them again, so simply combine nodes from all sentences
        new_doc = reconstruct_rich_docx(sentences, redlines=False)

    # Write to file
    with zipfile.ZipFile(temp_docx, mode='r') as zin, \
            zipfile.ZipFile(result_docx, mode='w',
                            compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename not in [
                DOCX_DOCUMENT_FNAME, DOCX_COMMENTS_FNAME,
                DOCX_CONTENTTYPES_FNAME, DOCX_RELS_FNAME
            ]:
                zout.writestr(item, zin.read(item.filename))
        zout.writestr(DOCX_DOCUMENT_FNAME, new_doc.encode('utf-8'))
        zout.writestr(DOCX_COMMENTS_FNAME, new_comments.encode('utf-8'))
        zout.writestr(DOCX_CONTENTTYPES_FNAME, new_contenttypes.encode('utf-8'))
        zout.writestr(DOCX_RELS_FNAME, new_rels.encode('utf-8'))

    result_docx.seek(0)

    return result_docx


def add_annotations_to_docx(temp_docx, sentences, included_annotations, from_plain=False, tz_name=None):
    """
    Check if there are any annotations we can add to exported docx and
    add them if yes.
    """

    annotations = get_annotations(sentences, included_annotations)

    if not annotations:
        return temp_docx

    initial_comments = None
    initial_contenttypes = None
    initial_rels = None
    result_docx = StringIO()

    with zipfile.ZipFile(temp_docx, mode='r') as zin:
        for name in zin.namelist():
            if name == DOCX_COMMENTS_FNAME:
                initial_comments = contentsdecode(zin.read(name))
            elif name == DOCX_CONTENTTYPES_FNAME:
                initial_contenttypes = contentsdecode(zin.read(name))
            elif name == DOCX_RELS_FNAME:
                initial_rels = contentsdecode(zin.read(name))
            elif name == DOCX_DOCUMENT_FNAME:
                initial_doc = contentsdecode(zin.read(name))
            elif name == DOCX_SETTINGS_FNAME:
                initial_settings = contentsdecode(zin.read(name))

    if not initial_comments:
        # There are no comment file in initial document, so we need
        # to initialize it and also add relations and content type
        initial_comments = get_basic_comments_xml()
        if not initial_contenttypes:
            initial_contenttypes = get_basic_contenttypes()
        if not initial_rels:
            initial_rels = get_basic_rels()
        new_contenttypes, new_rels = add_comment_relations(
            initial_contenttypes, initial_rels)
    else:
        # We can use existing relations
        new_contenttypes, new_rels = initial_contenttypes, initial_rels

    # Add annotation logo image relations
    new_contenttypes, new_rels, img_rid = add_image_relations(
        new_contenttypes, new_rels, ANNOTATION_IMG_NAME)

    new_comments = get_comments_xml(initial_comments, annotations, tz_name)

    if from_plain:
        new_doc = add_annotations_to_doc(annotations, initial_doc, sentences,
                                         img_rid)
    else:
        min_img_id = find_min_img_id(initial_doc)
        add_annotations_formatting(sentences, annotations, img_rid, min_img_id)
        # Redlines were already added, and there is no need to compute diffs
        # and restore them again, so simply combine nodes from all sentences
        new_doc = reconstruct_rich_docx(sentences, redlines=False)

    # Add Add xmlns drawing tags to word/settings.xml
    new_settings = add_xmlns_tags_to_settings(initial_settings)

    # Write to file
    with zipfile.ZipFile(temp_docx, mode='r') as zin, \
        zipfile.ZipFile(result_docx, mode='w',
                        compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename not in [
                DOCX_DOCUMENT_FNAME, DOCX_COMMENTS_FNAME,
                DOCX_CONTENTTYPES_FNAME, DOCX_RELS_FNAME,
                DOCX_SETTINGS_FNAME
            ]:
                zout.writestr(item, zin.read(item.filename))
        zout.writestr(DOCX_DOCUMENT_FNAME, new_doc.encode('utf-8'))
        zout.writestr(DOCX_COMMENTS_FNAME, new_comments.encode('utf-8'))
        zout.writestr(DOCX_CONTENTTYPES_FNAME, new_contenttypes.encode('utf-8'))
        zout.writestr(DOCX_RELS_FNAME, new_rels.encode('utf-8'))
        zout.writestr(DOCX_SETTINGS_FNAME, new_settings.encode('utf-8'))
        zout.write(ANNOTATION_IMG_FILE, 'word/media/%s' % ANNOTATION_IMG_NAME)

    result_docx.seek(0)

    return result_docx
