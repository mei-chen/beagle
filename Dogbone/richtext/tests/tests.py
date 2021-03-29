# -*- coding: utf-8 -*-
import bs4
import mock
import os
import time
from random import shuffle
from unittest import TestCase

from core.models import Document, Sentence
from django.contrib.auth.models import User
from richtext import importing, exporting
from richtext.xmldiff import (
    preserve_xml_space,
    apply_sentences_to_nodes,
    fix_runs_nodes, remove_superfluous_runs,
    create_numbering_counter, get_formatted_numbering,
    reconstruct_xml, nodes_to_plaintext,
    tokenize_xml, diff_change_sentence,
    get_comments_from_docx, get_ordered_comments_list, get_new_comments,
    get_comments_xml, get_basic_comments_xml, add_comment_formatting,
    _add_comment_ids, add_comments_to_doc, add_comment_to_xml,
    add_comment_relations, get_basic_contenttypes, get_basic_rels,
    get_annotations, format_annotation, merge_multiple_annotations,
    add_image_relations, add_annotations_formatting, add_annotations_to_doc,
    add_xmlns_tags_to_sentence, add_xmlns_tags_to_parsed_doc,
    add_xmlns_tags_to_settings, find_min_img_id,
    remove_doc_annotations, remove_comments_annotations, remove_image_relations,
    fix_comments_dates
)
from nlplib.utils import split_sentences, markers_to_linebreaks


TEST_TXT = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'MasterAgreement.txt')
TEST_DOCX = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'MasterAgreement.docx')
TEST_DOC = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'MasterAgreement.doc')
TEST_PDF = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'MasterAgreement.pdf')


def _sentsplit_formatted(txtrich):
    # Generate the nodes format
    nodes = tokenize_xml(txtrich)
    # Get (space preserving) plaintext
    plaintext = nodes_to_plaintext(nodes)
    # Split the plaintext into sentences
    txtsentences = split_sentences(plaintext)
    # Construct nodes format split into sentences (from sentence split plaintext and raw nodes format)
    node_sentences = apply_sentences_to_nodes(txtsentences, nodes)
    # Close/open Runs at sentence boundary
    return remove_superfluous_runs(fix_runs_nodes(node_sentences))


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, data, headers):
            self.raw = data
            self.ok = True
            if headers and headers['Authorization'] == 'Bearer bad_token':
                self.ok = False

        def iter_content(self, chunk_size=1):
            def generate():
                while True:
                    chunk = self.raw.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            return generate()

    if args[0] == 'file://%s' % TEST_DOCX:
        headers = kwargs.get('headers')
        return MockResponse(open(TEST_DOCX), headers)
    else:
        return MockResponse('')


def mocked_doc_to_docx(filename):
    return TEST_DOCX


def mocked_pdf_to_docx(filename):
    return TEST_DOCX


class DocxTest(TestCase):
    """ Tests for xmldiff module. """

    def test_preserve_xml_space(self):
        self.assertEqual('w:p', preserve_xml_space('w:p'))
        self.assertEqual('w:r', preserve_xml_space('w:r'))

        self.assertEqual('w:t xml:space="preserve"',
                         preserve_xml_space('w:t'))
        self.assertEqual('w:t name="value" xml:space="preserve"',
                         preserve_xml_space('w:t name="value"'))
        self.assertEqual('w:t xml:space="preserve" name="value"',
                         preserve_xml_space('w:t xml:space="preserve" name="value"'))
        self.assertEqual('w:t xml:space="preserve" name="value"',
                         preserve_xml_space('w:t xml:space="default" name="value"'))

        self.assertEqual('w:delText xml:space="preserve"',
                         preserve_xml_space('w:delText'))
        self.assertEqual('w:delText name="value" xml:space="preserve"',
                         preserve_xml_space('w:delText name="value"'))
        self.assertEqual('w:delText xml:space="preserve" name="value"',
                         preserve_xml_space('w:delText xml:space="preserve" name="value"'))
        self.assertEqual('w:delText xml:space="preserve" name="value"',
                         preserve_xml_space('w:delText xml:space="default" name="value"'))

    def test_tokenize_xml(self):
        """ Test XML text to list of XML nodes. """

        expected_result = [
            (u'w:p xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"', 'o'),
            (u'w:pPr', 'o'),
            (u'w:pStyle w:val="P1"/', 'o'),
            (u'w:pPr', 'c'),
            (u'w:r', 'o'),
            (u'w:t', 'o'),
            (u"This is first sentence. I'm second sentence. This is ", 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:rPr', 'o'),
            (u'w:rStyle w:val="T1"/', 'o'),
            (u'w:rPr', 'c'),
            (u'w:t', 'o'),
            (u'bold', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:t', 'o'),
            (u' text. This is ', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:rPr', 'o'),
            (u'w:rStyle w:val="T1"/', 'o'),
            (u'w:rPr', 'c'),
            (u'w:t', 'o'),
            (u'bold', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:t', 'o'),
            (u' and ', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:rPr', 'o'),
            (u'w:rStyle w:val="T2"/', 'o'),
            (u'w:rPr', 'c'),
            (u'w:t', 'o'),
            (u'underlined', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:t', 'o'),
            (u' text. This is ', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:rPr', 'o'),
            (u'w:rStyle w:val="T3"/', 'o'),
            (u'w:rPr', 'c'),
            (u'w:t', 'o'),
            (u'bold-italic', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:r', 'o'),
            (u'w:t', 'o'),
            (u' text.', 't'),
            (u'w:t', 'c'),
            (u'w:r', 'c'),
            (u'w:p', 'c')]
        result = tokenize_xml(u'''<w:p xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"><w:pPr><w:pStyle w:val="P1"/></w:pPr><w:r><w:t>This is first sentence. I'm second sentence. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> text. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> and </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T2"/></w:rPr><w:t>underlined</w:t></w:r><w:r><w:t> text. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T3"/></w:rPr><w:t>bold-italic</w:t></w:r><w:r><w:t> text.</w:t></w:r></w:p>''')
        self.assertListEqual(expected_result, result)

    def test_tokenize_other_text_xml(self):
        xml = '''<tag1>text_1</tag1>\t<tag2>text_2</tag2>'''
        actual_nodes = tokenize_xml(xml)
        expected_nodes = [('tag1', 'o'), ('text_1', 'ot'), ('tag1', 'c'),
                          ('tag2', 'o'), ('text_2', 'ot'), ('tag2', 'c')]
        self.assertEqual(expected_nodes, actual_nodes)

    @staticmethod
    def _create_document():
        if not User.objects.filter(username='user_for_xmldiff_test'):
            test_user = User.objects.create(username='user_for_xmldiff_test',
                                            email='user_for_xmldiff_test@test.test')
            id = test_user.id
        else:
            id = User.objects.get(username='user_for_xmldiff_test').id

        document = Document.objects.create(owner_id=id)
        document.init([])
        document.save()
        return document

    @staticmethod
    def _add_comments_to_document(document, timestamp, count=2):
        for i in range(1, count + 1):
            formatting = [('w:r', 'o'), ('w:t', 'o'), ('Sentence %s.' % i, 't'), ('w:t', 'c'), ('w:r', 'c')]
            sent = Sentence.objects.create(text='Sentence %s.' % i,
                                           doc=document,
                                           modified_by=document.owner,
                                           formatting=formatting)
            document.sentences_ids.append(sent.id)
            sent.add_comment(document.owner,
                             'Comment %s' % i,
                             timestamp=timestamp)

    def test_formatted_sent_split_reconstruct(self):
        """ Test xml decomposition and reconstruction """

        samplexml = u'''<w:r><w:rPr><w:i/></w:rPr><w:t>Rights to Use the Services.</w:t></w:r><w:r><w:t xml:space="preserve">  Subject to the terms set forth in this Agreement, We grant to </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>You</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> a limited, nonexclusive, non-t</w:t></w:r><w:r><w:t>ransferable license to use the Services that You enroll for.  You agree: (</w:t></w:r><w:proofErr w:type="spellStart"/><w:r><w:t>i</w:t></w:r><w:proofErr w:type="spellEnd"/><w:r><w:t>) the Services contain proprietary and confidential information that belongs to Us, Our licensors or suppliers, other customers, and/or other third parties; and (ii) the Services an</w:t></w:r><w:r><w:t>d such proprietary and confidential information are protected by laws, including, but not limited to, laws relating to patents, copyrights, trademarks, trade secrets, other proprietary and intellectual property rights, unfair competition, and privacy right</w:t></w:r><w:r><w:t>s and laws (collectively, “Proprietary Rights”).  You agree to use the Services solely for Your own benefit or otherwise in accordance with the purpose of Your organization set forth in Your governing documents (i.e. articles of incorporation, letters pate</w:t></w:r><w:r><w:t xml:space="preserve">nt, constitution, trust document, act of Parliament, or such other applicable document).  We retain all right, title and interest in the Services and Our Content. </w:t></w:r></w:p><w:p w:rsidR="00813AEB" w:rsidRDefault="00901C2A"><w:pPr><w:numPr><w:ilvl w:val="1"/><w:numId w:val="1"/></w:numPr><w:ind w:right="8" w:hanging="449"/></w:pPr><w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">Fees for Services. </w:t></w:r><w:r><w:t>You agree to pay all applicable fees and other amounts that are applicabl</w:t></w:r><w:r><w:t xml:space="preserve">e to </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>Your</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> use of the Services, which are set out in the Virtual Change® Service Terms and Our Donation Transfer and Fee Policy. </w:t></w:r></w:p><w:p w:rsidR="00813AEB" w:rsidRDefault="00901C2A"><w:pPr><w:numPr><w:ilvl w:val="1"/><w:numId w:val="1"/></w:numPr><w:spacing w:after="0"/><w:ind w:right="8" w:hanging="449"/></w:pPr>'''
        output = reconstruct_xml(tokenize_xml(samplexml))
        self.assertEqual(samplexml, output)

    def test_nodes_to_plaintext(self):
        """ Test xml to plaintext """

        samplexml = u'''<w:r><w:t>Order is executed by Customer. Unless either Party provides </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>thirty (30) days</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> written notice of termination priorto the expiration of the initial term, and any subsequent term, this Agreement shall automatically renew at Blackfoot's then current fees for an additional 1-year term for all Services except that it will automatically renew for 1-month term for Voice-Over-IP Services.</w:t></w:r>'''
        sampleplain = u'''Order is executed by Customer. Unless either Party provides thirty (30) days written notice of termination priorto the expiration of the initial term, and any subsequent term, this Agreement shall automatically renew at Blackfoot's then current fees for an additional 1-year term for all Services except that it will automatically renew for 1-month term for Voice-Over-IP Services.'''
        self.assertEqual(nodes_to_plaintext(tokenize_xml(samplexml)),
                         sampleplain)

    def test_apply_sents_to_xmlnodes(self):
        """ Test sentences apply to xml nodes """

        samplexml = u'''<w:r><w:t>Order is executed by Customer. Unless either Party provides </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>thirty (30) days</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> written notice of termination priorto the expiration of the initial term, and any subsequent term, this Agreement shall automatically renew at Blackfoot's then current fees for an additional 1-year term for all Services except that it will automatically renew for 1-month term for Voice-Over-IP Services.</w:t></w:r>'''
        sentsxml = ['<w:r><w:t>Order is executed by Customer. ', 'Unless either Party provides </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>thirty (30) days</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> written notice of termination priorto the expiration of the initial term, and any subsequent term, this Agreement shall automatically renew at Blackfoot\'s then current fees for an additional 1-year term for all Services except that it will automatically renew for 1-month term for Voice-Over-IP Services.</w:t></w:r>']
        nodes = tokenize_xml(samplexml)
        plaintext = nodes_to_plaintext(nodes)
        txtsentences = split_sentences(plaintext)
        node_sentences = apply_sentences_to_nodes(txtsentences, nodes)
        self.assertEqual(list(map(reconstruct_xml, node_sentences)), sentsxml)

    def test_fix_runs_nodes(self):
        """ Test closing/opening runs at sentence boundary. """

        txtsentences = split_sentences(u"This is first sentence. I'm second sentence. This is bold text. This is bold and underlined text. This is bold-italic text.\n")
        nodes = tokenize_xml(u'''<w:p xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"><w:pPr><w:pStyle w:val="P1"/></w:pPr><w:r><w:t>This is first sentence. I'm second sentence. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> text. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> and </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T2"/></w:rPr><w:t>underlined</w:t></w:r><w:r><w:t> text. This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T3"/></w:rPr><w:t>bold-italic</w:t></w:r><w:r><w:t> text.</w:t></w:r></w:p>''')
        node_sentences = apply_sentences_to_nodes(txtsentences, nodes)
        node_sentences = fix_runs_nodes(node_sentences)
        sentsxml = list(map(reconstruct_xml, node_sentences))
        expected = [
            u'<w:p xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"><w:pPr><w:pStyle w:val="P1"/></w:pPr><w:r><w:t>This is first sentence. </w:t></w:r>',
            u"<w:r><w:t>I'm second sentence. </w:t></w:r>",
            u'<w:r><w:t>This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> text. </w:t></w:r>',
            u'<w:r><w:t>This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T1"/></w:rPr><w:t>bold</w:t></w:r><w:r><w:t> and </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T2"/></w:rPr><w:t>underlined</w:t></w:r><w:r><w:t> text. </w:t></w:r>',
            u'<w:r><w:t>This is </w:t></w:r><w:r><w:rPr><w:rStyle w:val="T3"/></w:rPr><w:t>bold-italic</w:t></w:r><w:r><w:t> text.</w:t></w:r></w:p>']
        self.assertListEqual(expected, sentsxml)

    def test_rich_diff_add_at_the_end(self):
        srich = (
            '<w:r><w:t>Unless either Party provides </w:t></w:r>'
            '<w:proofErr w:type="gramStart"/><w:r><w:t>thirty (30) days</w:t>'
            '</w:r><w:proofErr w:type="gramEnd"/><w:r>'
            '<w:t xml:space="preserve"> written notice of termination priorto '
            'the expiration of the initial term')
        stok = _sentsplit_formatted(srich)[0]
        sorig = nodes_to_plaintext(stok)
        added = ' more content.'
        smod = sorig + added

        sent_nodes = diff_change_sentence(sorig, smod, stok)
        self.assertEquals(reconstruct_xml(sent_nodes), srich + added + '</w:t></w:r>')

    def test_rich_diff_spaces_break(self):
        """
        Spaces either at the beginning or at the end of the sentence in xml
        that were not persisted in the plaintext (on which diff was applied)
        would break the export.
        """

        stok = [[u'w:p w14:paraId="0E91A8FA" w14:textId="05471E38" w:rsidR="00DA7619" w:rsidRDefault="00DA7619" w:rsidP="00E631FA"', u'o'], [u'w:pPr', u'o'], [u'w:pStyle w:val="2-LevelLegal2"/', u'o'], [u'w:jc w:val="both"/', u'o'], [u'w:rPr', u'o'], [u'w:rFonts w:eastAsia="MS Mincho"/', u'o'], [u'w:b/', u'o'], [u'w:bCs/', u'o'], [u'w:i/', u'o'], [u'w:iCs/', u'o'], [u'w:lang w:val="en-CA"/', u'o'], [u'w:rPr', u'c'], [u'w:pPr', u'c'], [u'w:bookmarkStart w:id="31" w:name="_DV_M29"/', u'o'], [u'w:bookmarkEnd w:id="31"/', u'o'], [u'w:r w:rsidRPr="00E631FA"', u'o'], [u'w:rPr', u'o'], [u'w:rFonts w:eastAsia="MS Mincho"/', u'o'], [u'w:b/', u'o'], [u'w:bCs/', u'o'], [u'w:lang w:val="en-CA"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u' Taxes.  ', u't'], [u'w:t', u'c'], [u'w:r', u'c']]
        stokafter = [[u'w:p w14:paraId="0E91A8FA" w14:textId="05471E38" w:rsidR="00DA7619" w:rsidRDefault="00DA7619" w:rsidP="00E631FA"', u'o'], [u'w:pPr', u'o'], [u'w:pStyle w:val="2-LevelLegal2"/', u'o'], [u'w:jc w:val="both"/', u'o'], [u'w:rPr', u'o'], [u'w:rFonts w:eastAsia="MS Mincho"/', u'o'], [u'w:b/', u'o'], [u'w:bCs/', u'o'], [u'w:i/', u'o'], [u'w:iCs/', u'o'], [u'w:lang w:val="en-CA"/', u'o'], [u'w:rPr', u'c'], [u'w:pPr', u'c'], [u'w:bookmarkStart w:id="31" w:name="_DV_M29"/', u'o'], [u'w:bookmarkEnd w:id="31"/', u'o'], [u'w:r w:rsidRPr="00E631FA"', u'o'], [u'w:rPr', u'o'], [u'w:rFonts w:eastAsia="MS Mincho"/', u'o'], [u'w:b/', u'o'], [u'w:bCs/', u'o'], [u'w:lang w:val="en-CA"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u' Taxeffffs.  ', u't'], [u'w:t', u'c'], [u'w:r', u'c']]
        sorig = u'Taxes.'
        smod = u'Taxeffffs.'

        sent_nodes = diff_change_sentence(sorig, smod, stok)
        self.assertEquals(sent_nodes, stokafter)

    def test_rich_diff_additional_linebreaks(self):
        old_text = 'Part 1 (paragraph 1)\nPart 2 (paragraph 1)\n\nPart 3 (paragraph 2)'
        new_text = 'Part_1, and some new text here (paragraph_1)\nPart-2 (paragraph-1)\n\nPart #3, and yet another new text (paragraph #2)'

        input_nodes = [
            ['w:p', 'o'], ['w:t', 'o'], ['Part 1 (paragraph 1)', 't'], ['w:t', 'c'], ['w:br/', 'o'], ['w:t', 'o'], ['Part 2 (paragraph 1)', 't'], ['w:t', 'c'], ['w:p', 'c'],
            ['w:br/', 'o'],
            ['w:p', 'o'], ['w:t', 'o'], ['Part 3 (paragraph 2)', 't'], ['w:t', 'c'], ['w:p', 'c']
        ]
        expected_output_nodes = [
            ['w:p', 'o'], ['w:t', 'o'], ['Part_1, and some new text here (paragraph_1)', 't'], ['w:t', 'c'], ['w:br/', 'o'], ['w:t', 'o'], ['Part-2 (paragraph-1)', 't'], ['w:t', 'c'], ['w:p', 'c'],
            ['w:br/', 'o'],
            ['w:p', 'o'], ['w:t', 'o'], ['Part #3, and yet another new text (paragraph #2)', 't'], ['w:t', 'c'], ['w:p', 'c']
        ]

        actual_output_nodes = diff_change_sentence(old_text, new_text, input_nodes)
        self.assertEqual(expected_output_nodes, actual_output_nodes)

    def test_rich_diff_preserve_leading_and_trailing_spaces(self):
        old_text = 'Some old sentence. Yet another sentence!'
        new_text = 'Some new sentence. Yet another sentence?'

        input_nodes = [
            ['w:t', 'o'], ['  Some old sentence. ', 't'], ['w:t', 'c'],
            ['w:t', 'o'], ['Yet another sentence!   ', 't'], ['w:t', 'c'],
        ]
        expected_output_nodes = [
            ['w:t', 'o'], ['  Some new sentence. ', 't'], ['w:t', 'c'],
            ['w:t', 'o'], ['Yet another sentence?   ', 't'], ['w:t', 'c'],
        ]

        actual_output_nodes = diff_change_sentence(old_text, new_text, input_nodes)
        self.assertEqual(expected_output_nodes, actual_output_nodes)

    def test_rich_diff_with_redlines(self):
        txt_old = 'Terms and Conditions'
        txt_new = 'Terms or Conditions'

        fmt_old = [
            ['w:r', 'o'],
                ['w:rPr', 'o'], ['w:rFonts w:ascii="Times New Roman"', 'o'], ['w:sz w:val="20"', 'o'], ['w:b w:val="true"', 'o'], ['w:u w:val="dash"', 'o'], ['w:rPr', 'c'],
                ['w:t', 'o'], ['Terms and Conditions', 't'], ['w:t', 'c'],
            ['w:r', 'c']
        ]
        fmt_new_expected = [
            ['w:r', 'o'],
                ['w:rPr', 'o'], ['w:rFonts w:ascii="Times New Roman"', 'o'], ['w:sz w:val="20"', 'o'], ['w:b w:val="true"', 'o'], ['w:u w:val="dash"', 'o'], ['w:rPr', 'c'],
                ['w:t', 'o'], ['Terms ', 't'], ['w:t', 'c'],
            ['w:r', 'c'],

            ['w:del w:author="Gevorg Davoian" w:date="1/11/2017 14:13" w:id="1"', 'o'],
                ['w:r', 'o'],
                    ['w:rPr', 'o'], ['w:rFonts w:ascii="Times New Roman"', 'o'], ['w:sz w:val="20"', 'o'], ['w:b w:val="true"', 'o'], ['w:u w:val="dash"', 'o'], ['w:rPr', 'c'],
                    ['w:delText', 'o'], ['and', 'dt'], ['w:delText', 'c'],
                ['w:r', 'c'],
            ['w:del', 'c'],

            ['w:ins w:author="Gevorg Davoian" w:date="1/11/2017 14:13" w:id="2"', 'o'],
                ['w:r', 'o'],
                    ['w:rPr', 'o'], ['w:rFonts w:ascii="Times New Roman"', 'o'], ['w:sz w:val="20"', 'o'], ['w:b w:val="true"', 'o'], ['w:u w:val="dash"', 'o'], ['w:rPr', 'c'],
                    ['w:t', 'o'], ['or', 't'], ['w:t', 'c'],
                ['w:r', 'c'],
            ['w:ins', 'c'],

            ['w:r', 'o'],
                ['w:rPr', 'o'], ['w:rFonts w:ascii="Times New Roman"', 'o'], ['w:sz w:val="20"', 'o'], ['w:b w:val="true"', 'o'], ['w:u w:val="dash"', 'o'], ['w:rPr', 'c'],
                ['w:t', 'o'], [' Conditions', 't'], ['w:t', 'c'],
            ['w:r', 'c']
        ]

        fmt_new_actual = diff_change_sentence(
            txt_old, txt_new, fmt_old,
            redlines=True, author='Gevorg Davoian', date='1/11/2017 14:13', ids={'del': 1, 'ins': 2}
        )
        self.assertEqual(fmt_new_expected, fmt_new_actual)

    def test_space_around_quotes(self):
        srich = (
            '<w:r><w:t>This Master Subscription Agreement (the "</w:t></w:r><w:r><w:rPr>'
            '<w:rFonts w:eastAsia="MS Mincho"/><w:b/><w:bCs/></w:rPr>'
            '<w:t>Agreement</w:t></w:r><w:r><w:rPr>'
            '<w:rFonts w:eastAsia="MS Mincho"/></w:rPr>'
            '<w:t xml:space="preserve">") is entered into</w:t></w:r>'
        )
        splain = (
            'This Master Subscription Agreement (the "Agreement")'
            ' is entered into'
        )
        stok = _sentsplit_formatted(srich)[0]
        stransf = nodes_to_plaintext(stok)

        self.assertEquals(stransf, splain)

    def test_bullets_nonsplit(self):
        """
        Make sure bad-split merging works for formatted text too
        """
        srich = '''<w:p w:rsidR="00A14EC5" w:rsidRDefault="00A14EC5" w:rsidP="00A14EC5"><w:pPr><w:keepNext/><w:tabs><w:tab w:val="center" w:pos="0"/></w:tabs><w:suppressAutoHyphens/><w:spacing w:after="240"/><w:rPr><w:b/><w:color w:val="000000"/><w:spacing w:val="-2"/><w:sz w:val="20"/></w:rPr></w:pPr></w:p> <w:p w:rsidR="00A14EC5" w:rsidRDefault="00A14EC5" w:rsidP="00A14EC5"><w:pPr><w:keepNext/><w:tabs><w:tab w:val="center" w:pos="0"/></w:tabs><w:suppressAutoHyphens/><w:spacing w:after="240"/><w:rPr><w:bCs/><w:color w:val="000000"/><w:spacing w:val="-2"/><w:sz w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:b/><w:color w:val="000000"/><w:spacing w:val="-2"/><w:sz w:val="20"/></w:rPr><w:t>4. </w:t></w:r> <w:r><w:rPr><w:b/><w:color w:val="000000"/><w:spacing w:val="-2"/><w:sz w:val="20"/></w:rPr><w:tab/><w:t xml:space="preserve">Development Schedule.  </w:t></w:r>'''
        splain = '4. Development Schedule.'
        stok = _sentsplit_formatted(srich)[0]
        stransf = nodes_to_plaintext(stok)

        self.assertEquals(stransf.strip(), splain)

    def test_rich_diff_spaces_inside(self):
        stok = [[u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'The Landlord shall, within fourteen (14) ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="002C4F0C"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'business ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'days after receipt of such request, notify the Tenant in writi', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="002C4F0C"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'ng either that: (a) the Weber', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u' consents or does not consent, as the case may be; or (b) ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="006A6EC3"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'Weber ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'elects to cancel and terminate this ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00A0179D"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'Agreement.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:p', u'c']]
        stokafter = [[u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'Weber shall, within fourteen (14) ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="002C4F0C"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'business ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'days after receipt of such request, notify the Tenant in writi', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="002C4F0C"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'ng either that: (a) the Weber', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u' consents or does not consent, as the case may be; or (b) ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="006A6EC3"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'Weber ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00FB6498" w:rsidRPr="00FB6498"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t xml:space="preserve"', u'o'], [u'elects to cancel and terminate this ', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:r w:rsidR="00A0179D"', u'o'], [u'w:rPr', u'o'], [u'w:sz w:val="22"/', u'o'], [u'w:szCs w:val="22"/', u'o'], [u'w:rPr', u'c'], [u'w:t', u'o'], [u'Agreement.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:p', u'c']]
        sorig = 'The Landlord shall, within fourteen (14) business days after receipt of such request, notify the Tenant in writing either that: (a) the Weber consents or does not consent, as the case may be; or (b) Weber elects to cancel and terminate this Agreement.'
        smod = 'Weber shall, within fourteen (14) business days after receipt of such request, notify the Tenant in writing either that: (a) the Weber consents or does not consent, as the case may be; or (b) Weber elects to cancel and terminate this Agreement.'

        sent_nodes = diff_change_sentence(sorig, smod, stok)
        self.assertEquals(sent_nodes, stokafter)

    def test_full_import_export_workflow(self):
        """ Test full workflow """
        samplexml = u'''<w:r><w:rPr><w:i/></w:rPr><w:t>Rights to Use the Services. </w:t></w:r> <w:r><w:t xml:space="preserve">Subject to the terms set forth in this Agreement, We grant to </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>You</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> a limited, nonexclusive, non-t</w:t></w:r><w:r><w:t>ransferable license to use the Services that You enroll for. You agree: (</w:t></w:r><w:proofErr w:type="spellStart"/><w:r><w:t>i</w:t></w:r><w:proofErr w:type="spellEnd"/><w:r><w:t>) the Services contain proprietary and confidential information that belongs to Us, Our licensors or suppliers, other customers, and/or other third parties; and (ii) the Services an</w:t></w:r><w:r><w:t>d such proprietary and confidential information are protected by laws, including, but not limited to, laws relating to patents, copyrights, trademarks, trade secrets, other proprietary and intellectual property rights</w:t></w:r>'''
        resultxml = u'''<w:r><w:rPr><w:i/></w:rPr><w:t>Rights to Use the Services. </w:t></w:r><w:r><w:t xml:space="preserve">Subject to the terms set forth in this Agreement, We grant to </w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>You</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:t xml:space="preserve"> a limited, nonexclusive, non-t</w:t></w:r><w:r><w:t>ransferable license to use the Services that You enroll for. </w:t></w:r><w:r><w:t>You agree: (</w:t></w:r><w:proofErr w:type="spellStart"/><w:r><w:t>i</w:t></w:r><w:proofErr w:type="spellEnd"/><w:r><w:t>) the Services contain proprietary and confidential information that belongs to Us, Our licensors or suppliers, other customers, and/or other third parties; and (ii) the Services an</w:t></w:r><w:r><w:t>d such proprietary and confidential information are protected by laws, including, but not limited to, laws relating to patents, copyrights, trademarks, trade secrets, other proprietary and intellectual property rights</w:t></w:r>'''
        xmlsentences = _sentsplit_formatted(samplexml)

        nodes = []
        for spk in xmlsentences:
            for n in spk:
                nodes.append(n)
                if n[0].endswith('.'):
                    nodes.append((' ', 't'))
        newdoc = reconstruct_xml(nodes)
        newdoc = markers_to_linebreaks(newdoc).encode('utf-8')

        self.assertEqual(resultxml, newdoc)

    def test_get_comments_from_docx(self):
        decoded_comments = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r<w:comments xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"><w:comment w:author="Dmitriy Uvarenkov" w:id="1" w:date="2016-12-09T22:11:44Z"><w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" w:rsidRDefault="00000000" w:rsidRPr="00000000"><w:pPr><w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:widowControl w:val="0"/><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/><w:ind w:left="0" w:right="0" w:firstLine="0"/><w:contextualSpacing w:val="0"/><w:jc w:val="left"/></w:pPr><w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/><w:b w:val="0"/><w:i w:val="0"/><w:smallCaps w:val="0"/><w:strike w:val="0"/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:u w:val="none"/><w:vertAlign w:val="baseline"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">Mine too!</w:t></w:r></w:p></w:comment><w:comment w:author="Dmitriy Uvarenkov" w:id="2" w:date="2016-12-09T17:34:15Z"><w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" w:rsidRDefault="00000000" w:rsidRPr="00000000"><w:pPr><w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:widowControl w:val="0"/><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/><w:ind w:left="0" w:right="0" w:firstLine="0"/><w:contextualSpacing w:val="0"/><w:jc w:val="left"/></w:pPr><w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/><w:b w:val="0"/><w:i w:val="0"/><w:smallCaps w:val="0"/><w:strike w:val="0"/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:u w:val="none"/><w:vertAlign w:val="baseline"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">Second commented sentence</w:t></w:r></w:p></w:comment><w:comment w:author="Dmitriy Uvarenkov" w:id="3" w:date="2016-12-09T17:34:33Z"><w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" w:rsidRDefault="00000000" w:rsidRPr="00000000"><w:pPr><w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:widowControl w:val="0"/><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/><w:ind w:left="0" w:right="0" w:firstLine="0"/><w:contextualSpacing w:val="0"/><w:jc w:val="left"/></w:pPr><w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/><w:b w:val="0"/><w:i w:val="0"/><w:smallCaps w:val="0"/><w:strike w:val="0"/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:u w:val="none"/><w:vertAlign w:val="baseline"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">Commented range</w:t></w:r></w:p></w:comment><w:comment w:author="Dmitriy Uvarenkov" w:id="0" w:date="2016-12-09T22:11:21Z"><w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" w:rsidRDefault="00000000" w:rsidRPr="00000000"><w:pPr><w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:widowControl w:val="0"/><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/><w:ind w:left="0" w:right="0" w:firstLine="0"/><w:contextualSpacing w:val="0"/><w:jc w:val="left"/></w:pPr><w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/><w:b w:val="0"/><w:i w:val="0"/><w:smallCaps w:val="0"/><w:strike w:val="0"/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:u w:val="none"/><w:vertAlign w:val="baseline"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">My favorite sentence!</w:t></w:r></w:p></w:comment></w:comments>'
        result = get_comments_from_docx(decoded_comments)
        expected = {
            u'1': {'timestamp': 1481321504.0, 'author': u'Dmitriy Uvarenkov', 'text': u'Mine too!'},
            u'0': {'timestamp': 1481321481.0, 'author': u'Dmitriy Uvarenkov', 'text': u'My favorite sentence!'},
            u'3': {'timestamp': 1481304873.0, 'author': u'Dmitriy Uvarenkov', 'text': u'Commented range'},
            u'2': {'timestamp': 1481304855.0, 'author': u'Dmitriy Uvarenkov', 'text': u'Second commented sentence'}
        }
        self.assertDictEqual(expected, result)

    def test_get_ordered_comments_list(self):
        fixed_node_sentences = [
            [(u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/', 'o'), (u'w:color w:val="00000a"/', 'o'), (u'w:rtl w:val="0"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u"I'm ", 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/', 'o'), (u'w:color w:val="00000a"/', 'o'), (u'w:u w:val="single"/', 'o'), (u'w:rtl w:val="0"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'underlined', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/', 'o'), (u'w:color w:val="00000a"/', 'o'), (u'w:rtl w:val="0"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'. ', 't'), ('w:t', 'c'), ('w:r', 'c')],
            [(u'w:commentRangeStart w:id="2"/', 'o'), (u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/', 'o'), (u'w:color w:val="00000a"/', 'o'), (u'w:rtl w:val="0"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u"I'm second commented sentence", 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:commentRangeEnd w:id="2"/', 'o'), (u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:commentReference w:id="2"/', 'o'), (u'w:r', 'c'), (u'w:r w:rsidDel="00000000" w:rsidR="00000000" w:rsidRPr="00000000"', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/', 'o'), (u'w:color w:val="00000a"/', 'o'), (u'w:rtl w:val="0"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'. ', 't'), ('w:t', 'c'), ('w:r', 'c')]
        ]
        comments = {u'2': {'timestamp': 1481304855.0, 'author': u'Dmitriy Uvarenkov', 'text': u'Second commented sentence'}}
        result = get_ordered_comments_list(fixed_node_sentences, comments)
        expected = [[], [(u"Second commented sentence", 1481304855.0, u"Dmitriy Uvarenkov")]]
        self.assertListEqual(expected, result)

    def test_paragraph_and_linebreak_handling(self):
        xml_snippet = '<w:p><w:t>Sentence 1, paragraph 1.</w:t><w:br/><w:t>Sentence 2, paragraph 1.</w:t></w:p><w:br/><w:p><w:t>Sentence 3, paragraph 2.</w:t></w:p>'
        expected_nodes = [('w:p', 'o'), ('w:t', 'o'), ('Sentence 1, paragraph 1.', 't'), ('w:t', 'c'), ('w:br/', 'o'), ('w:t', 'o'), ('Sentence 2, paragraph 1.', 't'), ('w:t', 'c'), ('w:p', 'c'), ('w:br/', 'o'), ('w:p', 'o'), ('w:t', 'o'), ('Sentence 3, paragraph 2.', 't'), ('w:t', 'c'), ('w:p', 'c')]
        actual_nodes = tokenize_xml(xml_snippet)
        self.assertEqual(expected_nodes, actual_nodes)
        expected_plaintext = 'Sentence 1, paragraph 1.\nSentence 2, paragraph 1.\n\nSentence 3, paragraph 2.\n'
        actual_plaintext = nodes_to_plaintext(actual_nodes)
        self.assertEqual(expected_plaintext, actual_plaintext)
        expected_sentences = ['Sentence 1, paragraph 1.\n',
                              'Sentence 2, paragraph 1.\n\n',
                              'Sentence 3, paragraph 2.\n']
        actual_sentences = split_sentences(actual_plaintext)
        self.assertEqual(expected_sentences, actual_sentences)
        expected_node_sentences = [[('w:p', 'o'), ('w:t', 'o'), ('Sentence 1, paragraph 1.', 't'), ('w:t', 'c'), ('w:br/', 'o')],
                                   [('w:t', 'o'), ('Sentence 2, paragraph 1.', 't'), ('w:t', 'c'), ('w:p', 'c'), ('w:br/', 'o')],
                                   [('w:p', 'o'), ('w:t', 'o'), ('Sentence 3, paragraph 2.', 't'), ('w:t', 'c'), ('w:p', 'c')]]
        actual_node_sentences = apply_sentences_to_nodes(actual_sentences, actual_nodes)
        self.assertEqual(expected_node_sentences, actual_node_sentences)

    def test_get_new_comments(self):
        document = self._create_document()
        timestamp = int(time.time())
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        comment_dicts = [sent_com_dict[spk] for spk in sorted(sent_com_dict.keys())]
        for com_dict in comment_dicts:
            for comment in com_dict:
                del comment['uuid']
        expected = [
            [{'message': 'Comment 1', 'author': 'user_for_xmldiff_test', 'timestamp': timestamp}],
            [{'message': 'Comment 2', 'author': 'user_for_xmldiff_test', 'timestamp': timestamp}],
        ]
        self.assertListEqual(expected, comment_dicts)

    def test_add_comment_to_xml(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()
        _add_comment_ids(initial_xml, sent_com_dict)
        comment = sent_com_dict[min(sent_com_dict.keys())][0]

        parsed_comment_xml = bs4.BeautifulSoup(initial_xml, features='xml')
        add_comment_to_xml(parsed_comment_xml, comment)
        expected = u'<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T11:19:00+00:00" w:id="1"><w:p><w:r><w:t>Comment 1</w:t></w:r></w:p></w:comment></w:comments>'
        self.assertEqual(expected, str(parsed_comment_xml))

        tz_name = 'Europe/Kiev'
        parsed_comment_xml_tz_aware = bs4.BeautifulSoup(initial_xml, features='xml')
        add_comment_to_xml(parsed_comment_xml_tz_aware, comment, tz_name)
        expected_tz_aware = u'<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T13:19:00+02:00" w:id="1"><w:p><w:r><w:t>Comment 1</w:t></w:r></w:p></w:comment></w:comments>'
        self.assertEqual(expected_tz_aware, str(parsed_comment_xml_tz_aware))

    def test_get_comments_xml(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()

        comments_xml = get_comments_xml(initial_xml, sent_com_dict)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T11:19:00+00:00" w:id="1"><w:p><w:r><w:t>Comment 1</w:t></w:r></w:p></w:comment><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T11:19:00+00:00" w:id="2"><w:p><w:r><w:t>Comment 2</w:t></w:r></w:p></w:comment></w:comments>'
        self.assertEqual(expected, comments_xml)

        tz_name = 'Europe/Kiev'
        comments_xml_tz_aware = get_comments_xml(initial_xml, sent_com_dict, tz_name)
        expected_tz_aware = '<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T13:19:00+02:00" w:id="1"><w:p><w:r><w:t>Comment 1</w:t></w:r></w:p></w:comment><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T13:19:00+02:00" w:id="2"><w:p><w:r><w:t>Comment 2</w:t></w:r></w:p></w:comment></w:comments>'
        self.assertEqual(expected_tz_aware, comments_xml_tz_aware)

    def test_get_comments_xml_timezone_aware(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()
        comments_xml = get_comments_xml(initial_xml, sent_com_dict)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T11:19:00+00:00" w:id="1"><w:p><w:r><w:t>Comment 1</w:t></w:r></w:p></w:comment><w:comment w:author="user_for_xmldiff_test" w:date="2016-12-19T11:19:00+00:00" w:id="2"><w:p><w:r><w:t>Comment 2</w:t></w:r></w:p></w:comment></w:comments>'
        self.assertEqual(expected, comments_xml)

    def test_add_comment_ids(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()
        _add_comment_ids(initial_xml, sent_com_dict)
        comments = []
        for spk in sorted(sent_com_dict.keys()):
            comments.extend(sent_com_dict[spk])
        result_ids = [comment['id'] for comment in comments]
        self.assertEqual(['1', '2'], result_ids)

    def test_add_comment_formatting(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()
        _add_comment_ids(initial_xml, sent_com_dict)
        add_comment_formatting(sentences, sent_com_dict)
        result = [sent.formatting for sent in sentences]
        expected = [
            [[u'w:commentRangeStart w:id="1"/', 'o'], [u'w:r', u'o'], [u'w:t', u'o'], [u'Sentence 1.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:commentRangeEnd w:id="1"/', 'o'], [u'w:r', 'o'], [u'w:commentReference w:id="1"/', 'o'], [u'w:r', 'c']],
            [[u'w:commentRangeStart w:id="2"/', 'o'], [u'w:r', u'o'], [u'w:t', u'o'], [u'Sentence 2.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:commentRangeEnd w:id="2"/', 'o'], [u'w:r', 'o'], [u'w:commentReference w:id="2"/', 'o'], [u'w:r', 'c']]
        ]
        self.assertListEqual(expected, result)

    def test_add_comments_to_doc(self):
        document = self._create_document()
        timestamp = 1482146340
        self._add_comments_to_document(document, timestamp)
        sentences = document.get_sorted_sentences()
        sent_com_dict = get_new_comments(sentences)
        initial_xml = get_basic_comments_xml()
        _add_comment_ids(initial_xml, sent_com_dict)
        initial_doc = '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?>\n<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mo="http://schemas.microsoft.com/office/mac/office/2008/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:mv="urn:schemas-microsoft-com:mac:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14"><w:body><w:sectPr w:rsidR="00FC693F" w:rsidRPr="0006063C" w:rsidSect="00034616"><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800" w:header="720" w:footer="720" w:gutter="0"/><w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr></w:body></w:document>'
        new_doc = exporting.reconstruct_docx(initial_doc, sentences)
        result_doc = add_comments_to_doc(sent_com_dict, new_doc, sentences)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:document mc:Ignorable="w14 wp14" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:mo="http://schemas.microsoft.com/office/mac/office/2008/main" xmlns:mv="urn:schemas-microsoft-com:mac:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:body><w:p><w:commentRangeStart w:id="1"/><w:r><w:t xml:space="preserve">Sentence 1. </w:t></w:r><w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r><w:commentRangeStart w:id="2"/><w:r><w:t xml:space="preserve">Sentence 2.</w:t></w:r><w:commentRangeEnd w:id="2"/><w:r><w:commentReference w:id="2"/></w:r></w:p><w:p><w:r><w:br w:type="page"/></w:r></w:p><w:sectPr w:rsidR="00FC693F" w:rsidRPr="0006063C" w:rsidSect="00034616"><w:pgSz w:h="15840" w:w="12240"/><w:pgMar w:bottom="1440" w:footer="720" w:gutter="0" w:header="720" w:left="1800" w:right="1800" w:top="1440"/><w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr></w:body></w:document>'
        self.assertEqual(expected, result_doc)

    def test_add_comment_relations(self):
        initial_contenttypes = get_basic_contenttypes()
        initial_rels = get_basic_rels()
        new_contenttypes, new_rels = add_comment_relations(
            initial_contenttypes, initial_rels)
        exp_contenttypes = '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml" PartName="/word/comments.xml"/></Types>'
        exp_rels = '<?xml version="1.0" encoding="utf-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="comments.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"/></Relationships>'
        self.assertEqual(exp_contenttypes, new_contenttypes)
        self.assertEqual(exp_rels, new_rels)

    def test_get_annotations(self):
        document = self._create_document()
        sent = Sentence.objects.create(text='Sentence text.',
                                       doc=document,
                                       modified_by=document.owner)
        document.sentences_ids.append(sent.id)
        sent.add_tag(document.owner, 'test-annotation-tag')
        sentences = document.get_sorted_sentences()
        sent_ann_dict = get_annotations(sentences, {'test-annotation-tag': True})
        annotation = sent_ann_dict[sent.id][0]
        del annotation['timestamp']
        expected = {'author': 'Beagle', 'message': 'test-annotation-tag'}
        self.assertEqual(expected, annotation)

    def test_format_annotation(self):
        document = self._create_document()
        sent = Sentence.objects.create(text='Sentence text.',
                                       doc=document,
                                       modified_by=document.owner)
        document.sentences_ids.append(sent.id)
        sent.add_tag(document.owner, 'test-annotation-tag')
        annotation = sent.annotations['annotations'][0]
        timestamp = int(time.time())
        formatted_annotation = format_annotation(annotation, timestamp)
        expected = {'author': 'Beagle',
                    'message': 'test-annotation-tag',
                    'timestamp': timestamp}
        self.assertEqual(expected, formatted_annotation)

    def test_merge_multiple_annotations(self):
        timestamp = int(time.time())
        annotations = [
            {'author': 'Beagle',
             'message': 'test-annotation-tag1',
             'timestamp': timestamp},
            {'author': 'Beagle',
             'message': 'test-annotation-tag2',
             'timestamp': timestamp}
        ]
        result = merge_multiple_annotations(annotations)
        expected = [
            {'author': 'Beagle',
             'message': 'test-annotation-tag1\n\ntest-annotation-tag2',
             'timestamp': timestamp}
        ]

        self.assertEqual(expected, result)

    def test_add_image_relations(self):
        initial_contenttypes = get_basic_contenttypes()
        initial_rels = get_basic_rels()
        image_name = 'image_001.png'
        new_contenttypes, new_rels, rId = add_image_relations(
            initial_contenttypes, initial_rels, image_name)
        exp_contenttypes = '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default ContentType="image/png" Extension="png"/></Types>'
        exp_rels = '<?xml version="1.0" encoding="utf-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="media/image_001.png" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"/></Relationships>'
        self.assertEqual(exp_contenttypes, new_contenttypes)
        self.assertEqual(exp_rels, new_rels)
        self.assertEqual('rId1', rId)

    @mock.patch('richtext.xmldiff.add_xmlns_tags_to_sentence',
                side_effect=mock.MagicMock())
    def test_add_annotations_formatting(self, mocked):
        document = self._create_document()
        sent = Sentence.objects.create(text='Sentence text.',
                                       doc=document,
                                       modified_by=document.owner,
                                       formatting=[
                                           ('w:r', 'o'),
                                           ('w:t', 'o'),
                                           ('Sentence text.', 't'),
                                           ('w:t', 'c'),
                                           ('w:r', 'c')])
        document.sentences_ids.append(sent.id)
        sent.add_tag(document.owner, 'test-annotation-tag')
        sentences = document.get_sorted_sentences()
        sent_ann_dict = get_annotations(sentences, {'test-annotation-tag': True})
        _add_comment_ids('', sent_ann_dict)
        add_annotations_formatting(sentences, sent_ann_dict, 'rId1', 0)
        annotated_formatting = sentences[0].formatting
        expected = [[u'w:r', u'o'], [u'w:t', u'o'], [u'Sentence text.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:commentRangeStart w:id="1"/', 'o'], [u'w:r', 'o'], [u'w:rPr', 'o'], [u'w:vertAlign w:val="superscript"/', 'o'], [u'w:rPr', 'c'], [u'w:drawing', 'o'], [u'wp:inline', 'o'], [u'wp:extent cx="238125" cy="161925"/', 'o'], [u'wp:docPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/', 'o'], [u'a:graphic', 'o'], [u'a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"', 'o'], [u'pic:pic', 'o'], [u'pic:nvPicPr', 'o'], [u'pic:cNvPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/', 'o'], [u'pic:cNvPicPr/', 'o'], [u'pic:nvPicPr', 'c'], [u'pic:blipFill', 'o'], [u'a:blip r:embed="rId1"/', 'o'], [u'a:srcRect b="0" l="0" r="0" t="0"/', 'o'], [u'a:stretch', 'o'], [u'a:fillRect/', 'o'], [u'a:stretch', 'c'], [u'pic:blipFill', 'c'], [u'pic:spPr', 'o'], [u'a:xfrm', 'o'], [u'a:off x="0" y="0"/', 'o'], [u'a:ext cx="238125" cy="161925"/', 'o'], [u'a:xfrm', 'c'], [u'a:prstGeom prst="rect"/', 'o'], [u'a:ln/', 'o'], [u'pic:spPr', 'c'], [u'pic:pic', 'c'], [u'a:graphicData', 'c'], [u'a:graphic', 'c'], [u'wp:inline', 'c'], [u'w:drawing', 'c'], [u'w:r', 'c'], [u'w:commentRangeEnd w:id="1"/', 'o'], [u'w:r', 'o'], [u'w:commentReference w:id="1"/', 'o'], [u'w:r', 'c']]

        self.assertEqual(expected, annotated_formatting)

    @mock.patch('richtext.xmldiff.add_xmlns_tags_to_parsed_doc',
                side_effect=mock.MagicMock())
    def test_add_annotations_to_doc(self, mocked):
        document = self._create_document()
        sent = Sentence.objects.create(text='Sentence text.',
                                       doc=document,
                                       modified_by=document.owner,
                                       formatting=[
                                           ('w:r', 'o'),
                                           ('w:t', 'o'),
                                           ('Sentence text.', 't'),
                                           ('w:t', 'c'),
                                           ('w:r', 'c')])
        document.sentences_ids.append(sent.id)
        sent.add_tag(document.owner, 'test-annotation-tag')
        sentences = document.get_sorted_sentences()
        sent_ann_dict = get_annotations(sentences, {'test-annotation-tag': True})
        _add_comment_ids('', sent_ann_dict)
        initial_doc = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:sectPr/></w:body></w:document>'
        decoded_doc = exporting.reconstruct_docx(initial_doc, sentences)
        result = add_annotations_to_doc(sent_ann_dict, decoded_doc, sentences, 'rId1')
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t xml:space="preserve">Sentence text.</w:t></w:r><w:commentRangeStart w:id="1"/><w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:drawing><wp:inline><wp:extent cx="238125" cy="161925"/><wp:docPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId1"/><a:srcRect b="0" l="0" r="0" t="0"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="238125" cy="161925"/></a:xfrm><a:prstGeom prst="rect"/><a:ln/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r><w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r></w:p><w:p><w:r><w:br w:type="page"/></w:r></w:p><w:sectPr/></w:body></w:document>'

        self.assertEqual(expected, result)

    def test_add_xmlns_tags_to_sentence(self):
        document = self._create_document()
        sent = Sentence.objects.create(text='Sentence text.',
                                       doc=document,
                                       modified_by=document.owner,
                                       formatting=[
                                           ('w:document', 'o'),
                                           ('w:r', 'o'),
                                           ('w:t', 'o'),
                                           ('Sentence text.', 't'),
                                           ('w:t', 'c'),
                                           ('w:r', 'c'),
                                           ('w:document', 'c'),
                                       ])
        document.sentences_ids.append(sent.id)
        sentences = document.get_sorted_sentences()
        add_xmlns_tags_to_sentence(sentences[0])

        expected = [[u'w:document xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"', u'o'], [u'w:r', u'o'], [u'w:t', u'o'], [u'Sentence text.', u't'], [u'w:t', u'c'], [u'w:r', u'c'], [u'w:document', u'c']]
        self.assertEqual(expected, sentences[0].formatting)

    def test_add_xmlns_tags_to_parsed_doc(self):
        parsed = bs4.BeautifulSoup('<w:document/>', features='xml')
        add_xmlns_tags_to_parsed_doc(parsed)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<document xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"/>'
        self.assertEqual(expected, str(parsed))

    def test_add_xmlns_tags_to_settings(self):
        settings = '<w:settings/>'
        result = add_xmlns_tags_to_settings(settings)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<settings xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"/>'
        self.assertEqual(expected, result)

    def test_find_min_img_id(self):
        doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r<w:document xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">' \
              '<w:body><w:p><w:pPr><w:contextualSpacing w:val="0"/></w:pPr><w:r"><w:rPr><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">Sentence one. Some sentence with annotation.</w:t></w:r><w:r"><w:rPr><w:vertAlign w:val="superscript"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">annotation</w:t></w:r><w:r><w:drawing><wp:inline distB="114300" distT="114300" distL="114300" distR="114300"><wp:extent cx="238125" cy="161925"/><wp:effectExtent b="0" l="0" r="0" t="0"/><wp:docPr descr="beagle-logo_vector_tiny.png" id="1" name="image01.png"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr descr="beagle-logo_vector_tiny.png" id="1" name="image01.png"/><pic:cNvPicPr preferRelativeResize="0"/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId5"/><a:srcRect b="0" l="0" r="0" t="0"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="238125" cy="161925"/></a:xfrm><a:prstGeom prst="rect"/><a:ln/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r><w:r><w:drawing><wp:inline distB="114300" distT="114300" distL="114300" distR="114300"><wp:extent cx="238125" cy="161925"/><wp:effectExtent b="0" l="0" r="0" t="0"/><wp:docPr descr="beagle-logo_vector_tiny.png" id="20" name="image01.png"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr descr="beagle-logo_vector_tiny.png" id="20" name="image01.png"/><pic:cNvPicPr preferRelativeResize="0"/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId5"/><a:srcRect b="0" l="0" r="0" t="0"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="238125" cy="161925"/></a:xfrm><a:prstGeom prst="rect"/><a:ln/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r><w:r><w:rPr><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve"> Third sentence.</w:t></w:r></w:p><w:p><w:pPr><w:contextualSpacing w:val="0"/></w:pPr><w:r><w:rPr><w:rtl w:val="0"/></w:rPr></w:r></w:p><w:p><w:pPr><w:contextualSpacing w:val="0"/></w:pPr><w:r><w:rPr><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">Another paragraph.</w:t></w:r></w:p><w:sectPr><w:pgSz w:h="15840" w:w="12240"/><w:pgMar w:bottom="1440" w:top="1440" w:left="1440" w:right="1440"/><w:pgNumType w:start="1"/></w:sectPr></w:body>'
        result = find_min_img_id(doc)
        self.assertEqual(21, result)

    def test_remove_doc_annotations(self):
        doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14 wp14" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><w:body><w:p><w:pPr><w:pStyle w:val="Normal"/><w:rPr></w:rPr></w:pPr><w:r><w:rPr></w:rPr><w:t>London is the capital of Great Britain.</w:t></w:r><w:r><w:rPr></w:rPr><w:t xml:space="preserve"> </w:t></w:r><w:commentRangeStart w:id="1"/><w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:drawing><wp:inline><wp:extent cx="238125" cy="161925"/><wp:docPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr descr="Beagle annotation" id="0" name="beagle-logo_vector_tiny.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId5"/><a:srcRect b="0" l="0" r="0" t="0"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="238125" cy="161925"/></a:xfrm><a:prstGeom prst="rect"/><a:ln/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r><w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r> <w:r><w:rPr></w:rPr><w:t xml:space="preserve">Sentence 2.</w:t></w:r></w:p><w:sectPr><w:type w:val="nextPage"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:left="1134" w:right="1134" w:header="0" w:top="1134" w:footer="0" w:bottom="1134" w:gutter="0"/><w:pgNumType w:fmt="decimal"/><w:formProt w:val="false"/><w:textDirection w:val="lrTb"/><w:docGrid w:type="default" w:linePitch="240" w:charSpace="4294961151"/></w:sectPr></w:body></w:document>'
        result = remove_doc_annotations(doc)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:document mc:Ignorable="w14 wp14" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:body><w:p><w:pPr><w:pStyle w:val="Normal"/><w:rPr/></w:pPr><w:r><w:rPr/><w:t>London is the capital of Great Britain.</w:t></w:r><w:r><w:rPr/><w:t xml:space="preserve"> </w:t></w:r> <w:r><w:rPr/><w:t xml:space="preserve">Sentence 2.</w:t></w:r></w:p><w:sectPr><w:type w:val="nextPage"/><w:pgSz w:h="16838" w:w="11906"/><w:pgMar w:bottom="1134" w:footer="0" w:gutter="0" w:header="0" w:left="1134" w:right="1134" w:top="1134"/><w:pgNumType w:fmt="decimal"/><w:formProt w:val="false"/><w:textDirection w:val="lrTb"/><w:docGrid w:charSpace="4294961151" w:linePitch="240" w:type="default"/></w:sectPr></w:body></w:document>'
        self.assertEqual(expected, result)

    def test_remove_image_relations(self):
        rels = '<?xml version="1.0" encoding="utf-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="styles.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"/><Relationship Id="rId2" Target="fontTable.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"/><Relationship Id="rId3" Target="settings.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"/>\n<Relationship Id="rId4" Target="comments.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"/><Relationship Id="rId5" Target="media/beagle-logo_vector_tiny.png" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"/></Relationships>'
        result = remove_image_relations(rels)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="styles.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"/><Relationship Id="rId2" Target="fontTable.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"/><Relationship Id="rId3" Target="settings.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"/>\n<Relationship Id="rId4" Target="comments.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"/></Relationships>'
        self.assertEqual(expected, result)

    def test_remove_comments_annotations(self):
        comments = '<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:comment w:author="Beagle" w:date="2017-01-20T09:06:16" w:id="1"><w:p><w:r><w:t>annotation here</w:t></w:r></w:p></w:comment></w:comments>'
        result = remove_comments_annotations(comments)
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<w:comments xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" xmlns:lc="http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"/>'
        self.assertEqual(expected, result)

    def test_fix_comments_dates(self):
        comments = '\n'.join([
            '<?xml version="1.0" encoding="utf-8"?>',
            '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-03T11:41:13Z" w:id="0" w:initials="GD"/>',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-02T11:01:32Z" w:id="1" w:initials="GD"/>',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-01T11:39:21Z" w:id="2" w:initials="GD"/>',
            '</w:comments>',
        ])
        tz_name = 'Europe/Kiev'
        actual_new_comments = fix_comments_dates(comments, tz_name)
        expected_new_comments = '\n'.join([
            '<?xml version="1.0" encoding="utf-8"?>',
            '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-03T11:41:13+02:00" w:id="0" w:initials="GD"/>',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-02T11:01:32+02:00" w:id="1" w:initials="GD"/>',
            '<w:comment w:author="Gevorg Davoian" w:date="2017-03-01T11:39:21+02:00" w:id="2" w:initials="GD"/>',
            '</w:comments>',
        ])
        self.assertEqual(expected_new_comments, actual_new_comments)


def get_counter_values(counter, n):
    values = []
    for _ in range(n):
        values.append(counter.value)
        counter.increment()
    return values


class IndentlevelAndNumbering(TestCase):

    def test_none_counter(self):
        counter = create_numbering_counter()
        expected = [''] * 10
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_decimal_counter(self):
        counter = create_numbering_counter('decimal')
        expected = list(map(str, range(1, 11)))
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_upper_letter_counter(self):
        counter = create_numbering_counter('upperLetter', 22)
        expected = ['V', 'W', 'X', 'Y', 'Z', 'AA', 'BB', 'CC', 'DD', 'EE']
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_lower_letter_counter(self):
        counter = create_numbering_counter('lowerLetter', 22)
        expected = ['v', 'w', 'x', 'y', 'z', 'aa', 'bb', 'cc', 'dd', 'ee']
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_upper_roman_counter(self):
        counter = create_numbering_counter('upperRoman')
        expected = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_lower_roman_counter(self):
        counter = create_numbering_counter('lowerRoman')
        expected = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_unknown_counter(self):
        counter = create_numbering_counter('unknown')
        expected = [''] * 10
        actual = get_counter_values(counter, 10)
        self.assertEqual(expected, actual)

    def test_numbering_formatting(self):
        lvltext = '<[%1-%2]:(%3.%4)>'
        counters = [create_numbering_counter('upperRoman', 4, 0),
                    create_numbering_counter('upperLetter', 3, 1),
                    create_numbering_counter('decimal', 2, 2),
                    create_numbering_counter('decimal', 1, 3)]
        # The order of the counters inside the list doesn't matter,
        # since each one knows its own proper value for the indent-level
        shuffle(counters)
        expected = '<[IV-C]:(2.1)>'
        actual = get_formatted_numbering(lvltext, counters)
        self.assertEqual(expected, actual)

    def test_marked_docx_parsing(self):
        expected_txtsentences = [
            u'Master Agreement\n',
            u'This Master Agreement, including its Addenda and Schedules (\u201cMaster Agreement\u201d) governs terms and conditions between, [Client Name], [Client Address], a(n) [Client Location of Incorporation and Type of Organization] (\u201cClient\u201d) and [Desire2Learn entity name], [Desire2Learn Address], or its subsidiaries, divisions or affiliates (\u201cD2L\u201d) as listed in any Addendum to this Master Agreement.  \n',
            u'__/ILVL/0/__Definitions\n',
            u'__/ILVL/1/____/NBR/1.1/__Acceptable Use Policy means the applicable terms and conditions governing the use by End Users of a specific Product, Service or Application, as may be identified on the Fees and Rates Schedule.\n',
            u'__/ILVL/1/____/NBR/1.2/__Active User means a License Model that accounts for any person who registers for or is enrolled in one or more courses in each consecutive 12-month period following the Effective Date.  \n',
            u'__/ILVL/0/__Warranties\n',
            u'__/ILVL/1/____/NBR/2.1/__For Products and Services provided under this Agreement, D2L warrants that:\n__/ILVL/2/____/NBR/2.1.1/__The Software as provided under a License Addendum will substantially perform according to applicable Documentation provided that Client (or D2L at Client\u2019s request) has not modified the Software;\n__/ILVL/2/____/NBR/2.1.2/__The Applications and Cloud Service procured by Client under a Cloud Services Addendum will achieve in all material respects, the functionality described in the applicable Documentation; and\n__/ILVL/2/____/NBR/2.1.3/__Consulting Services shall be performed in accordance with industry standards and with the same level of care and skill as D2L provides to similarly-situated customers.\n',
            u'__/ILVL/1/____/NBR/2.2/__If Client purchases Hardware, D2L will provide a limited parts and labour warranty for a period of one (1) year from the shipment date of the Hardware (\u201cHardware Warranty Period\u201d), under the following terms:\n__/ILVL/2/____/NBR/2.2.1/__Hardware will substantially perform in the commercially reasonable manner expected to support Software or Applications provided that Client or any other entity under Client\u2019s implied or actual instruction has not attempted to, disassemble, modify or repair any portion of Hardware (\u201cQualifying Defect\u201d). ',
            u'After the Hardware Warranty Period, there is no warranty or condition of any kind on Hardware.\n',
            u'__/ILVL/2/____/NBR/2.2.2/__If D2L determines the existence of a Qualifying Defect, D2L shall: (a) authorize Client to ship the affected Hardware back to D2L or D2L\u2019s designated affiliate or partner at Client\u2019s own expense (FOB D2L or FOB D2L\u2019s designated affiliate or partner), (b) provide Client, directly or with a local third-party affiliate or partner, with onsite technical assistance to address the Qualifying Defect or, (c) provide Client with replacement  Hardware (FOB D2L or D2L\u2019s designated affiliate or partner).\n__/ILVL/0/__\n',
            u'Notice Information\n',
            u'[Desire2Learn]\n\n',
            u'[Client Name]\nTo:\nJohn Baker\n\n',
            u'To:\n\n',
            u'Title:\nPresident \n\n',
            u'Title:\n\n',
            u'Copy to:\nLegal Department\n\n',
            u'Fax:\n\n',
            u'Fax:\n519 772 0324\n\n',
            u'Phone:\n\n',
            u'Address:\n[address]\n\n',
            u'Address:\n\n\n\n\n',
            u'Email:\n\n\n'
        ]
        expected_node_sentences = [
            [(u'?xml version="1.0" encoding="UTF-8" standalone="yes"?', 'o'), (u'\n', 'ot'), (u'w:document xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"', 'o'), (u'w:body', 'o'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalTitle"/', 'o'), (u'w:spacing w:before="120" w:after="120"/', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:iCs/', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:bookmarkStart w:id="0" w:name="_GoBack"/', 'o'), (u'w:bookmarkEnd w:id="0"/', 'o'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:iCs/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Master Agreement', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:rPr', 'o'), (u'w:color w:val="FF0000"/', 'o'), (u'w:szCs w:val="16"/', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'This Master Agreement, including its Addenda and Schedules (\u201c', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:iCs/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Master Agreement', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'\u201d) governs terms and conditions between, [Client Name], [Client Address], a(n) [Client Location of Incorporation and Type of Organization] (\u201c', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:iCs/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Client', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'\u201d) and [Desire2Learn entity name], [Desire2Learn Address], or its subsidiaries, divisions or affiliates (\u201c', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:iCs/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'D2L', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'\u201d) as listed in any Addendum to this Master Agreement. ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:color w:val="FF0000"/', 'o'), (u'w:szCs w:val="16"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u' ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading1"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="0"/', 'o'), ('__/ILVL/0/__', 'm'), (u'w:numId w:val="1"/', 'o'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:bookmarkStart w:id="1" w:name="_Ref377553555"/', 'o'), (u'w:bookmarkEnd w:id="1"/', 'o'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Definitions', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading2"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="1"/', 'o'), ('__/ILVL/1/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/1.1/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Acceptable Use Policy', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u' means the applicable terms and conditions governing the use by End Users of a specific Product, Service or Application, as may be identified on the Fees and Rates Schedule.', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading2"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="1"/', 'o'), ('__/ILVL/1/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/1.2/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:i/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Active User', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u' ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:lang w:eastAsia="en-CA"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'means a License Model that ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'accounts for any person who registers for or is enrolled in one or more courses in each consecutive 12-month period following the Effective Date.  ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading1"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="0"/', 'o'), ('__/ILVL/0/__', 'm'), (u'w:numId w:val="1"/', 'o'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Warranties', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading2"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="1"/', 'o'), ('__/ILVL/1/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.1/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'For Products and Services provided under this Agreement, D2L warrants that:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="2"/', 'o'), ('__/ILVL/2/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.1.1/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'The Software as provided under a License Addendum will substantially perform according to applicable Documentation provided that Client (or D2L at Client\u2019s request) has not modified the Software;', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="2"/', 'o'), ('__/ILVL/2/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.1.2/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'The Applications and Cloud ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:cs="Arial"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'Service ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'procured by Client under a Cloud Services Addendum ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:cs="Arial"/', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'will achieve in all material respects, the functionality described in the ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'applicable ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rFonts w:cs="Arial"/', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Documentation', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'; and', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="2"/', 'o'), ('__/ILVL/2/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.1.3/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Consulting Services shall be performed in accordance with industry standards and with the same level of care and skill as D2L provides to similarly-situated customers.', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading2"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="1"/', 'o'), ('__/ILVL/1/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.2/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'If Client purchases Hardware, D2L will provide a limited parts and labour warranty for a period of one (1) year from the shipment date of the Hardware (\u201cHardware Warranty Period\u201d), under the following terms:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="2"/', 'o'), ('__/ILVL/2/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.2.1/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Hardware will substantially perform in the commercially reasonable manner expected to support Software or Applications provided that Client or any other entity under Client\u2019s implied or actual instruction has not attempted to, disassemble, modify or repair any portion of Hardware (\u201cQualifying Defect\u201d). ', 't'), ('w:t', 'c'), ('w:r', 'c')],
            [(u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'After the Hardware Warranty Period, there is no warranty or condition of any kind on Hardware.', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="2"/', 'o'), ('__/ILVL/2/__', 'm'), (u'w:numId w:val="1"/', 'o'), ('__/NBR/2.2.2/__', 'm'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'If D2L determines the existence of a Qualifying Defect, D2L shall: (a) authorize Client to ship the affected Hardware back to D2L or D2L\u2019s designated affiliate or partner at Client\u2019s own expense (FOB D2L or FOB D2L\u2019s designated affiliate or partner), (b) provide Client, directly or with a local third-party affiliate or partner, with onsite technical assistance to address the Qualifying Defect or, (c) provide Client with replacement  Hardware (FOB D2L or D2L\u2019s designated affiliate or partner).', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="MAHeading3"/', 'o'), (u'w:numPr', 'o'), (u'w:ilvl w:val="0"/', 'o'), ('__/ILVL/0/__', 'm'), (u'w:numId w:val="2"/', 'o'), (u'w:numPr', 'c'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="D2LSignature"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Notice Information', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tbl', 'o'), (u'w:tblPr', 'o'), (u'w:jc w:val="center"/', 'o'), (u'w:tblInd w:w="0" w:type="dxa"/', 'o'), (u'w:tblBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tblBorders', 'c'), (u'w:tblCellMar', 'o'), (u'w:top w:w="43" w:type="dxa"/', 'o'), (u'w:left w:w="115" w:type="dxa"/', 'o'), (u'w:bottom w:w="43" w:type="dxa"/', 'o'), (u'w:right w:w="115" w:type="dxa"/', 'o'), (u'w:tblCellMar', 'c'), (u'w:tblPr', 'c'), (u'w:tblGrid', 'o'), (u'w:gridCol w:w="902"/', 'o'), (u'w:gridCol w:w="3600"/', 'o'), (u'w:gridCol w:w="360"/', 'o'), (u'w:gridCol w:w="899"/', 'o'), (u'w:gridCol w:w="3968"/', 'o'), (u'w:tblGrid', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="576" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="4502" w:type="dxa"/', 'o'), (u'w:gridSpan w:val="2"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="D2LSignature"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="120" w:after="0"/', 'o'), (u'w:jc w:val="center"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'[Desire2Learn]', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="72" w:type="dxa"/', 'o'), (u'w:bottom w:w="72" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="Normal"/', 'o'), (u'w:keepNext/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="4867" w:type="dxa"/', 'o'), (u'w:gridSpan w:val="2"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="D2LSignature"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="120" w:after="0"/', 'o'), (u'w:jc w:val="center"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'[Client Name]', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="432" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'To:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'John Baker', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'To:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="432" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Title:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t xml:space="preserve"', 'o'), (u'President ', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Title:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:keepNext/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="432" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Copy to:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Legal Department', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Fax:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcMar', 'o'), (u'w:top w:w="130" w:type="dxa"/', 'o'), (u'w:tcMar', 'c'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="432" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Fax:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'519 772 0324', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Phone:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="804" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Address:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'[address]', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="left"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Address:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tr', 'o'), (u'w:trPr', 'o'), (u'w:trHeight w:val="432" w:hRule="exact"/', 'o'), (u'w:cantSplit w:val="false"/', 'o'), (u'w:trPr', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="902" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3600" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="360" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c')],
            [(u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="899" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="nil"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="nil"/', 'o'), (u'w:insideH w:val="nil"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:t', 'o'), (u'Email:', 't'), (u'w:t', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tc', 'o'), (u'w:tcPr', 'o'), (u'w:tcW w:w="3968" w:type="dxa"/', 'o'), (u'w:tcBorders', 'o'), (u'w:top w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:left w:val="nil"/', 'o'), (u'w:bottom w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:insideH w:val="single" w:sz="2" w:space="0" w:color="00000A"/', 'o'), (u'w:right w:val="nil"/', 'o'), (u'w:insideV w:val="nil"/', 'o'), (u'w:tcBorders', 'c'), (u'w:shd w:fill="FFFFFF" w:val="clear"/', 'o'), (u'w:vAlign w:val="bottom"/', 'o'), (u'w:tcPr', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:tc', 'c'), (u'w:tr', 'c'), (u'w:tbl', 'c'), (u'w:p', 'o'), (u'w:pPr', 'o'), (u'w:pStyle w:val="LegalBody"/', 'o'), (u'w:spacing w:before="0" w:after="60"/', 'o'), (u'w:jc w:val="both"/', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:pPr', 'c'), (u'w:r', 'o'), (u'w:rPr', 'o'), (u'w:rPr', 'c'), (u'w:r', 'c'), (u'w:p', 'c'), (u'w:sectPr', 'o'), (u'w:headerReference w:type="default" r:id="rId2"/', 'o'), (u'w:headerReference w:type="first" r:id="rId3"/', 'o'), (u'w:footerReference w:type="default" r:id="rId4"/', 'o'), (u'w:footerReference w:type="first" r:id="rId5"/', 'o'), (u'w:type w:val="nextPage"/', 'o'), (u'w:pgSz w:w="12240" w:h="15840"/', 'o'), (u'w:pgMar w:left="720" w:right="720" w:header="720" w:top="1800" w:footer="144" w:bottom="1440" w:gutter="0"/', 'o'), (u'w:pgNumType w:fmt="decimal"/', 'o'), (u'w:formProt w:val="false"/', 'o'), (u'w:titlePg/', 'o'), (u'w:textDirection w:val="lrTb"/', 'o'), (u'w:docGrid w:type="default" w:linePitch="360" w:charSpace="2047"/', 'o'), (u'w:sectPr', 'c'), (u'w:body', 'c'), (u'w:document', 'c')]
        ]
        actual_txtsentences, actual_node_sentences, _, _, _ = importing.parse_docx(TEST_DOCX)
        self.assertEqual(expected_txtsentences, actual_txtsentences)
        self.assertEqual(expected_node_sentences, actual_node_sentences)


class ImportingTest(TestCase):
    ''' Test importing module. '''

    def _create_document(self):
        if not User.objects.filter(username='user_for_import_test'):
            test_user = User.objects.create(username='user_for_import_test',
                                            email='for_import_test@test.test')
            id = test_user.id
        else:
            id = User.objects.get(username='user_for_import_test').id

        document = Document.objects.create(owner_id=id)
        document.save_docx = mock.MagicMock()
        document.save_pdf = mock.MagicMock()
        document.save_doc = mock.MagicMock()
        return document

    def test_get_named_styles_from_docx(self):
        """ Test styles.xml file parsing
        for named styles in a docx document. """
        named_styles = importing.get_named_styles_from_docx(TEST_DOCX)
        expected_styles = {
            '___DEFAULT___': {'size': 22},
            'CHSAHeading3': {'size': 16},
            'Heading3Char': {'bold': True,'size': 20},
            'CHSAHeading1': {'bold': True,'size': 16},
            'Annotationsubject': {'bold': True,'size': 20},
            'Heading2Char': {'bold': True,'size': 26},
            'Annotationreference': {'size': 16},
            'MBHeading1': {'bold': True,'size': 16},
            'MBHeading3': {'size': 16},
            'MBHeading2': {'size': 16},
            '00LegalTitleChar': {'bold': True,'size': 16},
            'FollowedHyperlink': {'underline': True},
            'CommentSubjectChar': {'bold': True,'size': 20},
            'LAHeading1': {'bold': True,'size': 16},
            'LAHeading2': {'size': 16},
            'HeaderChar': {},
            'Footnotereference': {},
            'Index': {},
            'VNTHeading1': {'bold': True,'size': 16},
            'VNTHeading3': {'size': 16},
            'VNTHeading2': {'size': 16},
            'BalloonText': {'size': 16},
            'CAHeading1': {'bold': True,'size': 16},
            'CAHeading2': {'size': 16},
            'CAHeading3': {'size': 16},
            'LegalTitle': {'size': 16},
            'BalloonTextChar': {'size': 16},
            'Heading2': {'bold': True,'size': 26},
            'Heading3': {'bold': True},
            'Heading1': {'bold': True,'size': 28},
            'FootnoteAnchor': {},
            'InternetLink': {'underline': True},
            'Footnotetext': {'size': 22},
            'LegalBodyBold': {'bold': True},
            'Footnote': {},
            '00Body': {'size': 16},
            'NoList': {},
            'ListParagraph': {'size': 22},
            'LAHeading1Char': {'bold': True,'size': 16},
            'Normal': {'size': 20},
            'CSHeading2': {'size': 16},
            'CSHeading3': {'size': 16},
            'CSHeading1': {'bold': True,'size': 16},
            'DRHeading2': {'size': 16},
            'DRHeading3': {'size': 16},
            'DRHeading1': {'bold': True,'size': 16},
            'DefaultParagraphFont': {},
            'MAHeading2': {'bold': False,'size': 16},
            'MAHeading3': {'bold': False,'size': 16},
            'MAHeading1': {'size': 16},
            '00AHHeading1': {'bold': True,'size': 16},
            'TextBody': {},
            'LegalBodyBullets': {},
            '00LegalTitle': {'size': 16},
            'MSSHeading2': {'size': 16},
            'MSSHeading3': {'size': 16},
            'MSSHeading1': {'bold': True,'size': 16},
            'LegalTitleChar': {'bold': True,'size': 16},
            '00AHHeading2': {'size': 16},
            'Googqstidbit1': {},
            'Googqstidbit0': {},
            'AHHeading3': {'size': 16},
            'AHHeading2': {'size': 16},
            'LegalBody': {'size': 16},
            'Heading': {'size': 28},
            'CHSAHeading2': {'size': 16},
            'FootnoteTextChar': {},
            'FirstPageFooter': {'size': 16},
            'MATitle': {'bold': True,'size': 16},
            'Header': {},
            'FooterChar': {'size': 16},
            'TableGrid': {'size': 20},
            'ListLabel14': {'bold': True},
            'ListLabel15': {'bold': False},
            'ListLabel12': {},
            'BodyTextChar': {},
            'ListLabel10': {'bold': True,'size': 16},
            'ListLabel11': {},
            'CommentTextChar': {'size': 16},
            'Footer': {'size': 16},
            'ListLabel13': {},
            'PlaceholderText': {},
            'List': {},
            'Caption': {'size': 24},
            'Annotationtext': {'size': 16},
            'SSHeading2': {'size': 16},
            'SSHeading3': {'size': 16},
            'SSHeading1': {'bold': True,'size': 16},
            'Heading1Char': {'bold': True,'size': 28},
            'D2LSignature': {'bold': True,'size': 16},
            'Style1AHA': {},
            'AHHeading1': {'bold': True,'size': 16},
            'LHeading3': {'size': 16},
            'LHeading2': {'size': 16},
            'LHeading1': {'bold': True,'size': 16},
            'ListLabel8': {},
            'ListLabel9': {'bold': True,'size': 16},
            'TableNormal': {},
            'ListLabel4': {'bold': False},
            'ListLabel5': {},
            'ListLabel6': {'bold': True,'size': 16},
            'ListLabel7': {'bold': False,'size': 16},
            'ListLabel1': {'bold': True,'size': 16},
            'ListLabel2': {'bold': True,'size': 16},
            'ListLabel3': {'bold': True}
        }
        self.assertDictEqual(expected_styles, named_styles)

    def test_source_handler_LocalUploader(self):
        """ Check if source_handler returns correct
        LocalUploader instance. """
        uploader = importing.source_handler('local')
        err_msg = 'Error: Received an upload request without attachment or URL'
        result_err = uploader.process()
        result = uploader.process(uploaded_file=open(TEST_DOCX))

        self.assertEqual((False, err_msg), result_err)
        self.assertTrue(result[0])

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_source_handler_URLUploader(self, mock_get):
        """ Check if source_handler returns correct
        URLUploader instance. """
        uploader = importing.source_handler('url')
        err_msg = 'Error: source is URL but file url not supplied'
        file_url = 'file://%s' % TEST_DOCX
        result_err = uploader.process()
        result = uploader.process(file_url=file_url)

        self.assertEqual((False, err_msg), result_err)
        self.assertTrue(result[0])

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_source_handler_GDriveUploader(self, mock_get):
        """ Check if source_handler returns correct
        GDriveUploader instance. """
        uploader = importing.source_handler('gdrive')
        err_msg1 = 'Bad access token'
        err_msg2 = 'Bad file URL, or Authorization problem'
        file_url = 'file://%s' % TEST_DOCX
        result_err1 = uploader.process()
        result_err2 = uploader.process(access_token='bad_token', file_url=file_url)
        result = uploader.process(access_token='good_token', file_url=file_url)

        self.assertEqual((False, err_msg1), result_err1)
        self.assertEqual((False, err_msg2), result_err2)
        self.assertTrue(result[0])

    def test_source_handler_InvalidUploader(self):
        """ Check if source_handler returns correct
        InvalidUploader instance. """
        uploader = importing.source_handler('foo')
        err_msg = 'Error: Invalid file upload source'
        result_err = uploader.process()

        self.assertEqual((False, err_msg), result_err)

    def test_conversion_handler_TxtConverter(self):
        """ Check if conversion_handler returns correct
        TxtConverter instance. """
        converter = importing.conversion_handler('.TXT')
        result = converter.process(None, TEST_TXT)

        self.assertTrue(result[0])

    def test_conversion_handler_DocXConverter(self):
        """ Check if conversion_handler returns correct
        DocXConverter instance. """
        converter = importing.conversion_handler('.DOCX')
        result = converter.process(self._create_document(), TEST_DOCX)

        self.assertTrue(result[0])

    @mock.patch('utils.conversion.doc_to_docx', side_effect=mocked_doc_to_docx)
    def test_conversion_handler_DocConverter(self, mock_doc_to_docx):
        """ Check if conversion_handler returns correct
        DocConverter instance. """
        converter = importing.conversion_handler('.DOC')
        result = converter.process(self._create_document(), TEST_DOC)
        # remove temporary file
        os.remove('%s.doc' % TEST_DOC)

        self.assertTrue(result[0])

    @mock.patch('utils.conversion.pdf_to_docx', side_effect=mocked_pdf_to_docx)
    def test_conversion_handler_PDFConverter(self, mock_pdf_to_docx):
        """ Check if conversion_handler returns correct
        PDFConverter instance. """
        converter = importing.conversion_handler('.PDF')
        result = converter.process(self._create_document(), TEST_PDF)
        # remove temporary file
        os.remove('%s.pdf' % TEST_PDF)

        self.assertTrue(result[0])

    def test_conversion_handler_InvalidConverter(self):
        """ Check if conversion_handler returns correct
        InvalidConverter instance. """
        converter = importing.conversion_handler('.AVI')
        err_msg = 'Document type not supported'
        result_err = converter.process(None, None)

        self.assertEqual((False, err_msg), result_err)
