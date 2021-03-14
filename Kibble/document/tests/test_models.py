import json
import os
import random
import string
import zipfile
from django.db.models.fields.files import FieldFile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from mock import patch, mock
from model_bakery import baker
from lxml.etree import fromstring, tostring
from unittest import skip

from document.models import Document, DocumentTag, Sentence
from document.tests.helpers import side_effect_tmpfile, TempCleanupTestCase
from portal.models import Batch, File
from utils.conversion import docx_to_txt


class ModelTest(TempCleanupTestCase):
    def setUp(self):
        self.tools = {
            'normalize (libreoffice)': Document.normalize_LO,
            'linebreakers': Document.linebreakers_cleanup,
            'title/header/footer': Document.title_header_footer_cleanup,
            'table of contents': Document.table_of_contents_cleanup,
            'bullet points and listing':
                Document.bullet_points_and_listing_cleanup,
            'listing rewriting': Document.listing_rewriting_cleanup,
            'tables': Document.tables_cleanup,
        }
        self.maxDiff = None

    def make_file(self, name='test.docx'):
        return SimpleUploadedFile(name, b'Test Content')

    def get_file(self, test_file):
        dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(dir, 'data', test_file)

    def make_document(self, test_file):
        content = open(self.get_file(test_file), 'r').read()
        return baker.make(Document, content_file=SimpleUploadedFile(
            'test.docx', content))

    @patch('document.models.docx_to_txt')
    def test_document_model_has_docx_and_text_file_fields(self, mock):
        """
        Document model should have docx and text fields
        """
        document = baker.make(Document)
        self.assertTrue(isinstance(document.content_file, FieldFile))
        self.assertTrue(isinstance(document.text_file, FieldFile))

    @patch('document.models.Document.get_content_file')
    @patch('document.models.docx_to_txt')
    def test_document_converts_file_to_text(self, convert_mock, file_mock):
        """
        Document should convert docx file to text one
        """
        convert_mock.side_effect = side_effect_tmpfile
        document = baker.make(Document, content_file=self.make_file())
        convert_mock.assert_called_once_with(file_mock.return_value.name)
        self.assertEqual(
            document.text_file.name,
            os.path.splitext(document.content_file.name)[0] + '.txt'
        )

    @patch('document.models.docx_to_txt')
    def test_document_ignores_conversion_errors(self, convert_mock):
        """
        Document should ignore conversion errors
        """
        convert_mock.return_value = None
        document = baker.make(Document, content_file=self.make_file())
        convert_mock.assert_called_once()
        self.assertEqual(document.text_file, None)

    @patch('document.models.Document.get_content_file')
    @patch('document.models.docx_to_txt')
    def test_document_converts_file_onchange(self, convert_mock, file_mock):
        """
        Document should run conversion on content file change
        """
        convert_mock.side_effect = side_effect_tmpfile
        document = baker.make(Document, content_file=self.make_file())
        convert_mock.reset_mock()
        old_name = document.text_file.name
        document.content_file = self.make_file()
        document.save()
        convert_mock.assert_called_once_with(file_mock.return_value.name)
        self.assertEqual(
            document.text_file.name,
            os.path.splitext(document.content_file.name)[0] + '.txt'
        )
        self.assertNotEqual(document.text_file.name, old_name)

    @patch('document.models.Document.get_content_file')
    @patch('document.models.docx_to_txt')
    def test_document_converts_file_on_assign(self, convert_mock, file_mock):
        """
        Document should run conversion on content file assignment
        """
        convert_mock.side_effect = side_effect_tmpfile
        document = baker.make(Document)
        convert_mock.assert_not_called()
        document.content_file = self.make_file()
        document.save()
        convert_mock.assert_called_once_with(file_mock.return_value.name)
        self.assertEqual(
            document.text_file.name,
            os.path.splitext(document.content_file.name)[0] + '.txt'
        )

    def test_no_such_tool(self):
        """
        cleanup_document_tools returns None if no tool is present
        """
        self.assertEqual(Document.get_tool('funny'), None)

    def test_get_all(self):
        """
        cleanup_document_tools returns dict of tools on no params
        """
        selected_tools = Document.get_tool()
        self.assertEqual(self.tools, selected_tools)

    def test_select_linebreakers_cleanup(self):
        """
        linebreakers_cleanup can be selected
        """
        selected_tools = Document.get_tool('linebreakers')
        self.assertEqual(self.tools['linebreakers'], selected_tools)

    def test_select_title_cleanup(self):
        """
        title_cleanup can be selected
        """
        selected_tools = Document.get_tool('title/header/footer')
        self.assertEqual(self.tools['title/header/footer'], selected_tools)

    def test_select_table_of_contents_cleanup(self):
        """
        table_of_contents_cleanup can be selected
        """
        selected_tools = Document.get_tool('table of contents')
        self.assertEqual(self.tools['table of contents'], selected_tools)

    def test_select_bullet_points_and_listing_cleanup(self):
        """
        bullet_points_and_listing_cleanup can be selected
        """
        selected_tools = Document.get_tool('bullet points and listing')
        self.assertEqual(
            self.tools['bullet points and listing'], selected_tools)

    def test_select_listing_rewriting_cleanup(self):
        """
        listing_rewriting_cleanup can be selected
        """
        selected_tools = Document.get_tool('listing rewriting')
        self.assertEqual(self.tools['listing rewriting'], selected_tools)

    def test_select_tables_cleanup(self):
        """
        tables_cleanup can be selected
        """
        selected_tools = Document.get_tool('tables')
        self.assertEqual(self.tools['tables'], selected_tools)

    @patch('document.models.Document.bullet_points_and_listing_cleanup')
    @patch('document.models.Document.title_header_footer_cleanup')
    def test_cleanup_create_tag(self, bpalc_mock, t_mock):
        """
        cleanup should create DocumentTag for document on cleanup call
        """
        bpalc_mock.return_value = baker.make(Document)
        t_mock.return_value = baker.make(Document)
        document = baker.make(Document)
        self.assertFalse(DocumentTag.objects.exists())

        document.cleanup(['title/header/footer'])
        self.assertTrue(
            DocumentTag.objects.filter(
                name='title/header/footer', document=document).exists()
        )

        document.cleanup(['bullet points and listing'])
        self.assertFalse(
            DocumentTag.objects.filter(
                name='title/header/footer', document=document).exists()
        )
        self.assertTrue(
            DocumentTag.objects.filter(
                name='bullet points and listing', document=document).exists()
        )

    @patch('document.models.Document.linebreakers_cleanup')
    @patch('document.models.Document.table_of_contents_cleanup')
    @patch('document.models.Document.tables_cleanup')
    def test_cleanup_create_tags_with_num(self, t1_mock, t2_mock, t3_mock):
        """
        cleanup on call creates tags with sequence order placed in order field
        """
        t1_mock.return_value = baker.make(Document)
        t2_mock.return_value = baker.make(Document)
        t3_mock.return_value = baker.make(Document)
        document = baker.make(Document)

        document.cleanup(['linebreakers', 'table of contents', 'tables'])
        self.assertEqual(
            DocumentTag.objects.filter(
                name='linebreakers', document=document).first().order, 0
        )
        self.assertEqual(
            DocumentTag.objects.filter(
                name='table of contents', document=document).first().order, 1
        )
        self.assertEqual(
            DocumentTag.objects.filter(
                name='tables', document=document).first().order, 2
        )

    @patch('document.models.Document.purge_tags')
    def test_pruge_on_cleanup(self, purge_mockup):
        """
        cleanup should call purge_tags
        """
        doc = baker.make(Document)
        doc.purge_tags()
        purge_mockup.assert_called_once()

    @patch('document.models.Document.table_of_contents_cleanup')
    def test_cleanup_recreate_tag(self, toc_mock):
        """
        cleanup should recreate tag on cleanup
        """
        toc_mock.return_value = True
        document = baker.make(Document)
        doctag = baker.make(
            DocumentTag, document=document, name='table of contents')

        self.assertEqual(DocumentTag.objects.count(), 1)

        document.cleanup(['table of contents'])

        self.assertEqual(DocumentTag.objects.count(), 1)
        first = DocumentTag.objects.first()
        self.assertEqual(first.name, 'table of contents')
        self.assertNotEqual(first, doctag)

    @patch('document.models.Document.table_of_contents_cleanup')
    def test_cleanup_doesnt_addd_tag_on_error(self, toc_mock):
        """
        cleanup should NOT create tag on error
        """
        toc_mock.return_value = None
        document = baker.make(Document)
        baker.make(DocumentTag, document=document, name='foo')

        self.assertEqual(DocumentTag.objects.count(), 1)

        document.cleanup(['table of contents'])

        self.assertFalse(DocumentTag.objects.exists())

    @patch('document.models.Document.conveyor')
    def test_process_called_on_cleanup(self, conveyor_mockup):
        """
        cleanup should call conveyor
        """
        document = baker.make(Document)
        document.cleanup(['title/header/footer'])
        conveyor_mockup.assert_called_once()

    def test_make_copy(self):
        """
        make_copy should copy document
        """
        doc = baker.make(Document)
        copied = doc.make_copy()

        self.assertNotEqual(doc.id, copied.id)
        self.assertEqual("Cleaned copy {}".format(doc.name), copied.name)

    def test_make_copy_remove_old_copy(self):
        """
        make_copy should remove old copy after call
        """
        doc = baker.make(Document)
        doc.make_copy()
        new_copied = doc.make_copy()

        filtered = Document.objects.get(origin=doc)
        self.assertEqual(filtered.id, new_copied.id)

    @patch('document.models.docx_to_txt')
    def test_make_copy_files(self, convert_mock):
        """
        make_copy should copy files
        """
        convert_mock.side_effect = side_effect_tmpfile
        file = ''.join(
            [random.choice(string.ascii_lowercase) for _ in range(10)]
        )
        doc = baker.make(
            Document,
            content_file=SimpleUploadedFile(file + '.docx', '1\n2\n3\n'),
            text_file=SimpleUploadedFile(file + '.txt', '1\n2\n3\n'),
        )
        copied = doc.make_copy()

        self.assertEqual('1\n2\n3\n', copied.text_file.read())
        self.assertEqual('1\n2\n3\n', copied.content_file.read())

        self.assertNotEqual(doc.content_file, copied.content_file)
        self.assertNotEqual(doc.text_file, copied.text_file)
        self.assertNotEqual(doc.content_file.name, copied.content_file.name)
        self.assertNotEqual(doc.text_file.name, copied.text_file.name)
        copied.delete()
        self.assertTrue(doc.content_file.size)
        self.assertTrue(doc.text_file.size)

    def test_purge_old_tags(self):
        """
        purge_tags drops all existing tags for document
        """
        doc = baker.make(Document)
        baker.make(DocumentTag, document=doc, name='title/header/footer')
        baker.make(DocumentTag, document=doc, name='tables')
        baker.make(
            DocumentTag, document=doc, name='bullet points and listing')

        doc.purge_tags()
        self.assertFalse(DocumentTag.objects.filter(document=doc).exists())

    @patch('document.models.docx_to_txt')
    def test_files_deleted_on_instance_delete(self, convert_mock):
        """
        Document files should be deleted when instance is deleted
        """
        convert_mock.side_effect = side_effect_tmpfile
        doc = baker.make(
            Document,
            content_file=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            text_file=SimpleUploadedFile('copy.txt', '1\n2\n3\n'),
        )
        doc_file = doc.content_file
        txt_file = doc.text_file
        self.assertTrue(doc_file.size)
        self.assertTrue(txt_file.size)
        doc.delete()
        self.assertRaises(Exception, lambda: doc_file.size)
        self.assertRaises(Exception, lambda: txt_file.size)

    @patch('document.models.docx_to_txt')
    def test_files_deleted_on_queryset_delete(self, convert_mock):
        """
        Document files should be deleted when doc dueryset is deleted
        """
        convert_mock.side_effect = side_effect_tmpfile
        doc = baker.make(
            Document,
            content_file=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            text_file=SimpleUploadedFile('copy.txt', '1\n2\n3\n'),
        )
        doc_file = doc.content_file
        txt_file = doc.text_file
        self.assertTrue(doc_file.size)
        self.assertTrue(txt_file.size)
        Document.objects.filter(pk=doc.pk).delete()
        self.assertRaises(Exception, lambda: doc_file.size)
        self.assertRaises(Exception, lambda: txt_file.size)

    @patch('utils.personal_data.find_personal_data')
    @patch('document.models.docx_to_txt')
    def test_files_deleted_on_batch_instance_delete(
            self, convert_mock, personal_data_mock):
        """
        Document files should be deleted when batch instance is deleted
        """
        convert_mock.side_effect = side_effect_tmpfile
        batch = baker.make(Batch, name='Bar')
        file_ = baker.make(
            File,
            content=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            batch=batch)
        doc = baker.make(
            Document,
            source_file=file_,
            content_file=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            text_file=SimpleUploadedFile('copy.txt', '1\n2\n3\n'),
        )
        doc_file = doc.content_file
        txt_file = doc.text_file
        self.assertTrue(doc_file.size)
        self.assertTrue(txt_file.size)
        batch.delete()
        self.assertRaises(Exception, lambda: doc_file.size)
        self.assertRaises(Exception, lambda: txt_file.size)

    @patch('utils.personal_data.find_personal_data')
    @patch('document.models.docx_to_txt')
    def test_files_deleted_on_batch_queryset_delete(
            self, convert_mock, personal_data_mock):
        """
        Document files should be deleted when batch dueryset is deleted
        """
        convert_mock.side_effect = side_effect_tmpfile
        batch = baker.make(Batch, name='Bar')
        file_ = baker.make(
            File,
            content=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            batch=batch)
        doc = baker.make(
            Document,
            source_file=file_,
            content_file=SimpleUploadedFile('copy.docx', '1\n2\n3\n'),
            text_file=SimpleUploadedFile('copy.txt', '1\n2\n3\n'),
        )
        doc_file = doc.content_file
        txt_file = doc.text_file
        self.assertTrue(doc_file.size)
        self.assertTrue(txt_file.size)
        Batch.objects.filter(pk=batch.pk).delete()
        self.assertRaises(Exception, lambda: doc_file.size)
        self.assertRaises(Exception, lambda: txt_file.size)

    def test_get_doc(self):
        """
        Document.get_doc methods should return a docx.Document instance
        """
        doc = self.make_document('title-plain.docx')
        self.assertTrue(hasattr(doc.get_doc(), 'paragraphs'))

    def test_get_text_lines_no_text_file(self):
        """
        Document.get_text_lines should return an empty array if doesn't have a txt file
        """
        doc = baker.make(Document)
        self.assertEqual(doc.get_text_lines(), [])

    def test_get_text_lines_has_text_file(self):
        """
        Document.get_text_lines should return array of txt lines
        """
        doc = self.make_document('title-plain.docx')
        self.assertTrue(doc.get_text_lines())

    @patch('document.models.Document.store_content')
    def test_store_doc(self, store_content_mock):
        """
        Should save docx.Document in io
        """
        doc = baker.make(Document)
        docx = mock.MagicMock()
        doc.store_doc(docx)
        store_content_mock.assert_called_once()

    def test_get_file_no_field(self):
        """
        Should return an empty temporary file
        """
        f = Document.get_file(None)
        self.assertFalse(f.read())


class CleanupToolsTest(TempCleanupTestCase):
    def setUp(self):
        self.maxDiff = None

    def get_file(self, test_file):
        dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(dir, 'data', test_file)

    def make_document(self, test_file):
        content = open(self.get_file(test_file), 'r').read()
        return baker.make(Document, content_file=SimpleUploadedFile(
            'test.docx', content))

    @patch('document.models.NotificationManager.notify_client')
    @patch('document.models.Document.make_copy')
    def test_conveyor_call_copy(self, make_copy_mock, notify_mock):
        """
        conveyor should call self.make_copy
        """
        document = baker.make(Document)
        make_copy_mock.return_value = self.make_document('title-plain.docx')

        document.conveyor(['tables'], 'foo')
        make_copy_mock.assert_called_once()
        notify_mock.assert_not_called()

    @patch('document.models.NotificationManager.notify_client')
    @patch('document.models.Document.make_copy')
    def test_conveyor_bad_tool(self, make_copy_mock, notify_mock):
        """
        conveyor should show warning on bad tool
        """
        document = baker.make(Document)
        make_copy_mock.return_value = self.make_document('title-plain.docx')
        document.conveyor(['foobar'], 'FooSession')
        make_copy_mock.assert_called_once()
        notify_mock.assert_called_once_with('FooSession', {
            'notify': {
                'level': 'warning',
                'message': 'Skip unknown tool "foobar"'
            },
        })

    @patch('document.models.Document.tables_cleanup')
    @patch('document.models.NotificationManager.notify_client')
    @patch('document.models.Document.make_copy')
    def test_conveyor_tool_error(self, make_copy_mock, notify_mock,
                                 cleanup_mock):
        """
        conveyor should show warning on tool error
        """
        cleanup_mock.return_value = None
        document = baker.make(Document)
        make_copy_mock.return_value = self.make_document('title-plain.docx')
        document.conveyor(['tables'], 'FooSession')
        make_copy_mock.assert_called_once()
        notify_mock.assert_called_once_with('FooSession', {
            'notify': {
                'level': 'warning',
                'message': 'Tool "tables" failed on %s!' % document.name
            },
        })

    def xml_content(self, document, xml):
        zip = zipfile.ZipFile(document)
        xml_tree = fromstring(zip.read(xml).strip())
        return tostring(xml_tree, pretty_print=True)

    def compare_files(self, doc, expected_file, check_xml=False):
        expected_name = self.get_file(expected_file)
        expected_file = docx_to_txt(expected_name)
        expected_content = open(expected_file, 'r').read()
        os.remove(expected_file)
        actual_content = doc.text_file.read()
        self.assertMultiLineEqual(expected_content, actual_content)
        if check_xml:
            self.assertMultiLineEqual(
                self.xml_content(expected_name, 'word/document.xml'),
                self.xml_content(doc.content_file, 'word/document.xml')
            )

    def test_cleanup_line_breaks_formatted(self):
        """
        Line breaks cleanup unittest for formatted text
        """
        doc = self.make_document('formatted-linebreaks.docx')
        doc.linebreakers_cleanup()
        self.compare_files(doc, 'formatted-linebreaks-cleaned.docx')

    def test_cleanup_line_breaks_plaintext(self):
        """
        Line breaks cleanup unittest for plaintext
        """
        doc = self.make_document('plaintext-linebreaks.docx')
        doc.linebreakers_cleanup()
        self.compare_files(doc, 'plaintext-linebreaks-cleaned.docx')

    def test_cleanup_line_breaks_blank_lists(self):
        """
        Line breaks cleanup unittest for blank list elements
        """
        doc = self.make_document('formatted-linebreaks-blank-list.docx')
        doc.linebreakers_cleanup()
        self.compare_files(doc, 'formatted-linebreaks-blank-list-cleaned.docx')

    def test_cleanup_list_formatted(self):
        """
        List cleanup unittest for formatted text
        """
        doc = self.make_document('formatted-lists.docx')
        doc.bullet_points_and_listing_cleanup()
        self.compare_files(doc, 'formatted-lists-cleaned.docx')

    def test_cleanup_list_plain(self):
        """
        List cleanup unittest for plaintext lists
        """
        doc = self.make_document('plaintext-lists.docx')
        doc.bullet_points_and_listing_cleanup()
        self.compare_files(doc, 'plaintext-lists-cleaned.docx')

    def test_cleanup_tables_formatted(self):
        """
        Tables cleanup unittest for formatted text
        """
        doc = self.make_document('formatted-tables.docx')
        doc.tables_cleanup()
        self.compare_files(doc, 'formatted-tables-cleaned.docx', True)

    def test_cleanup_tables_formatted_postprocessing(self):
        """
        Tables cleanup unittest for formatted text with postprocessing
        """
        doc = self.make_document('formatted-tables-postprocessing.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-cleaned.docx', True)

    def test_cleanup_tables_formatted_OCR(self):
        """
        Tables cleanup unittest for formatted text after OCR (broken)
        """
        doc = self.make_document('formatted-tables-ocr.docx')
        doc.tables_cleanup()

    def test_cleanup_rewriting_list_formatted(self):
        """
        List rewriting unittest for formatted text
        """
        doc = self.make_document('formatted-lists-rewritting.docx')
        doc.listing_rewriting_cleanup()
        self.compare_files(doc, 'formatted-lists-rewritting-cleaned.docx')

    def test_cleanup_rewriting_list_plain(self):
        """
        List rewriting unittest for plaintext lists
        """
        doc = self.make_document('plaintext-lists-rewritting.docx')
        doc.listing_rewriting_cleanup()
        self.compare_files(doc, 'plaintext-lists-rewritting-cleaned.docx')

    def test_cleanup_rewriting_multilevel_list_formatted(self):
        """
        List rewriting unittest for formatted text
        """
        doc = self.make_document('formatted-multilevel-lists-rewritting.docx')
        doc.listing_rewriting_cleanup()
        self.compare_files(
            doc, 'formatted-multilevel-lists-rewritting-cleaned.docx')

    def test_cleanup_rewriting_multilevel_list_plain(self):
        """
        List rewriting unittest for plaintext lists
        """
        doc = self.make_document('plaintext-multilevel-lists-rewritting.docx')
        doc.listing_rewriting_cleanup()
        self.compare_files(
            doc, 'plaintext-multilevel-lists-rewritting-cleaned.docx')

    def test_cleanup_tables_formatted_postprocessing_bold_header(self):
        """
        Tables cleanup unittest with postprocessing for bold header
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-header-bold.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-header-cleaned.docx')

    def test_cleanup_tables_formatted_postprocessing_color_header(self):
        """
        Tables cleanup unittest with postprocessing for colorized header
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-header-colorized.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-header-cleaned.docx')

    def test_cleanup_tables_formatted_postprocessing_no_header(self):
        """
        Tables cleanup unittest - no postprocessing for odd rows colorized
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-changed-rows-styles.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-noheader-cleaned.docx', True)

    def test_cleanup_tables_formatted_postprocessing_bold_vheader(self):
        """
        Tables cleanup unittest with postprocessing for bold vertical header
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-vheader-bold.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-vheader-cleaned.docx')

    def test_cleanup_tables_formatted_postprocessing_color_vheader(self):
        """
        Tables cleanup unittest with postprocessing for colorized vert.header
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-vheader-colorized.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-vheader-cleaned.docx')

    def test_cleanup_tables_formatted_postprocessing_no_vheader(self):
        """
        Tables cleanup unittest - no postprocessing for odd cols colorized
        """
        doc = self.make_document(
            'formatted-tables-postprocessing-changed-cols-styles.docx')
        doc.tables_cleanup()
        self.compare_files(
            doc, 'formatted-tables-postprocessing-novheader-cleaned.docx',
            True
        )

    @skip("Integration test, depends on libreoffice")
    def test_normalize_libreoffice(self):
        """
        LibreOffice normalization of broken documents
        """
        doc = self.make_document('formatted-bad-lists.docx')
        doc.normalize_LO()
        self.compare_files(
            doc, 'formatted-bad-lists-cleaned.docx'
        )

    @patch('document.models.Document.get_content_file')
    @patch('document.models.docx_to_txt')
    @patch('document.models.docx_libreoffice')
    def test_normalize_libreoffice_mocked(self, lo_mock, txt_mock, file_mock):
        """
        LibreOffice tool copies converted document to old file & runs docx2txt
        """
        txt_mock.side_effect = side_effect_tmpfile
        lo_mock.return_value = '/tmp/foo.docx'
        with open(lo_mock.return_value, 'w+'):
            pass
        doc = self.make_document('formatted-bad-lists.docx')
        txt_mock.reset_mock()
        doc.normalize_LO()
        lo_mock.assert_called_with(file_mock.return_value.name)
        txt_mock.assert_called_once_with(file_mock.return_value.name)
        self.assertEqual(doc.content_file.size, 0)

    @patch('document.models.Document.get_content_file')
    @patch('document.models.docx_to_txt')
    @patch('document.models.docx_libreoffice')
    def test_normalize_libreoffice_exception(self, lo_mock, txt_mock,
                                             file_mock):
        """
        LibreOffice tool handles case when file is not converted
        """
        txt_mock.side_effect = side_effect_tmpfile
        lo_mock.return_value = None
        doc = self.make_document('formatted-bad-lists.docx')
        txt_mock.reset_mock()
        doc.normalize_LO()
        lo_mock.assert_called_once_with(file_mock.return_value.name)
        txt_mock.assert_not_called()


class TableOfContentsCleanupTest(TestCase):
    def compare(self, clean_docx, doc):
        expected_file = docx_to_txt(self.get_path(clean_docx))
        expected_content = open(expected_file, 'r').read()
        os.remove(expected_file)
        actual_content = doc.text_file.read()
        self.assertMultiLineEqual(expected_content, actual_content)

    def get_path(self, fname):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', 'toc', fname
        )

    def make_doc(self, fpath):
        suf = SimpleUploadedFile('foo.docx', open(fpath).read())
        return baker.make(Document, content_file=suf, name='Foo')

    def do_docx_comparing(self, test_file):
        expected_file = '%s-clean.docx' % test_file
        test_file = '%s.docx' % test_file
        doc = self.make_doc(self.get_path(test_file))
        doc.table_of_contents_cleanup()
        self.compare(expected_file, doc)

    def test_formatted_keyword(self):
        """
        Examples
            Table Of Contents
            1. Foo
            2. Bar
        """
        self.do_docx_comparing('formatted_keyword')

    def test_formatted_duplicates(self):
        """
        Examples
            1. Foo 1
            2. Bar 2

            Foo
            Lorem ipsum
            Bar
            Dolor set amet
        """
        self.do_docx_comparing('formatted_duplicates')

    def test_plain_keyword(self):
        """
        Examples
            Table Of Contents
            Foo .............. 1
            Bar .............. 2
        """
        self.do_docx_comparing('plain_keywords')

    def test_plain_duplicates(self):
        """
        Examples
            Foo .............. 1
            Bar .............. 2

            Foo
            Lorem ipsum
            Bar
            Dolor set amet
        """
        self.do_docx_comparing('plain_duplicates')

    def test_plain_junk(self):
        """
        Remove junk in Table Of Contents
        Examples
            Table Of Contents
            1. Foo
            junk junk junk
            .dasw df...a afeef fca
            2. Bar
        """
        self.do_docx_comparing('plain_junk')

    def test_placement_middle(self):
        """
        Table Of Contents in the middle of a document
        """
        self.do_docx_comparing('plain_placement_middle')

    def test_placement_end(self):
        """
        Table Of Contents in the end of a document
        """
        self.do_docx_comparing('plain_placement_end')

    def test_table_keyword(self):
        """
        Examples
            Table Of Contents
            <DOCX TABLE>
        """
        self.do_docx_comparing('table_keyword')

    def test_generated(self):
        """
        Cleanup generated Table Of Contents
        """
        self.do_docx_comparing('generated')


class DocumentSentencesTest(TestCase):
    def setUp(self):
        self.documents = baker.make(Document, 3)
        self.sentences = baker.make(Sentence, 10, document=self.documents[0])
        self.sentences2 = baker.make(Sentence, 10, document=self.documents[1])

    def test_generate_csv(self):
        """
        If sentences for document exists then generate a csv from it
        """
        doc = Document.objects.get(pk=self.documents[0].id)
        csv = doc.get_csv()
        for s in self.sentences:
            self.assertIn(s.text, csv)
        for s in self.sentences2:
            self.assertNotIn(s.text, csv)

    def test_generate_csv_no_sentences(self):
        """
        Return non if document has no sentences
        """
        doc = Document.objects.get(pk=self.documents[2].id)
        csv = doc.get_csv()
        self.assertIsNone(csv)

    def test_generate_json(self):
        """
        If sentences for document exists then generate json from it
        """
        doc = Document.objects.get(pk=self.documents[0].id)
        data = json.loads(doc.get_json())
        expected = [s.text for s in self.sentences]
        self.assertEqual(data, expected)

    def test_generate_json_no_sentences(self):
        """
        Return none if document has no sentences
        """
        doc = Document.objects.get(pk=self.documents[2].id)
        data = json.loads(doc.get_json())
        self.assertEqual(data, [])


class HFTCleanupTest(TestCase):
    def compare(self, clean_docx, doc):
        expected_file = docx_to_txt(self.get_path(clean_docx))
        expected_content = open(expected_file, 'r').read()
        os.remove(expected_file)
        actual_content = doc.text_file.read()
        self.assertMultiLineEqual(expected_content, actual_content)

    def get_path(self, fname):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', 'hft', fname
        )

    def make_doc(self, fpath):
        suf = SimpleUploadedFile('foo.docx', open(fpath).read())
        return baker.make(Document, content_file=suf, name='Foo')

    def do_compare(self, fname):
        clean_file = '%s-clean.docx' % os.path.splitext(fname)[0]
        dirty_file = '%s.docx' % fname
        doc = self.make_doc(self.get_path(dirty_file))
        doc.title_header_footer_cleanup()
        self.compare(clean_file, doc)

    def test_cleanup_title_plain(self):
        """
        Test file after txt to docx converting
        """
        self.do_compare('plain')

    def test_cleanup_title_formatted(self):
        """
        Test cleanup titles in the formatted docx file
        """
        self.do_compare('formatted')
