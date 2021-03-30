# -*- coding: utf-8 -*-
import os
import zipfile
from io import StringIO, BytesIO
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.conf import settings
from django.test import TestCase
from mock import patch
from model_bakery import baker

from portal.models import File
from utils import personal_data
from utils.conversion import (
    docx_to_txt, pdf_to_docx, doc_to_docx, txt_to_docx,
    compress_to_zip, docx_libreoffice,
    get_filename_wo_ext
)
from utils.sentence_splitting.api import SentenceSplittingRemoteAPI


class ConvertTest(TestCase):
    @patch('utils.conversion.call')
    def test_docx_to_txt_calls_docx2txt(self, call_mock):
        """
        docx_to_txt should call docx2txt
        """
        call_mock.return_value = 0
        docx2txt = os.path.join(
            settings.BASE_DIR, 'utils', 'docx2txt', 'docx2txt.pl')
        docx_to_txt('/tmp/foo/bar.file.docx')
        call_mock.assert_called_once_with([
            'timeout', '-k', '30', '60',
            docx2txt, '/tmp/foo/bar.file.docx', '/tmp/foo/bar.file.txt'
        ])

    @patch('utils.conversion.call')
    def test_docx_to_txt_calls_returns_filename(self, call_mock):
        """
        docx_to_txt should return new filename
        """
        call_mock.return_value = 0
        ret = docx_to_txt('/tmp/foo/bar.file.docx')
        self.assertEqual(ret, '/tmp/foo/bar.file.txt')

    @patch('utils.conversion.call')
    def test_docx_to_txt_returns_none_on_errors(self, call_mock):
        """
        docx_to_txt should return none on convert error
        """
        call_mock.return_value = 1
        ret = docx_to_txt('/tmp/foo/bar.file.docx')
        self.assertEqual(ret, None)

    @patch('utils.conversion.call')
    def test_docx_libreoffice_calls_libreoffice(self, call_mock):
        """
        docx_libreoffice should call libreoffice
        """
        call_mock.return_value = 0
        docx_libreoffice('/tmp/foo/bar.file.docx')
        call_mock.assert_called_once_with([
            'timeout', '-k', '30', '60',
            'libreoffice', '--headless', '--convert-to', 'docx',
            '--outdir', '/tmp', '/tmp/foo/bar.file.docx'
        ])

    @patch('utils.conversion.call')
    def test_docx_libreoffice_calls_returns_filename(self, call_mock):
        """
        docx_libreoffice should return new filename
        """
        call_mock.return_value = 0
        with open('/tmp/bar.file.docx', 'w+'):
            pass
        ret = docx_libreoffice('/tmp/foo/bar.file.doc')
        self.assertEqual(ret, '/tmp/bar.file.docx')
        os.unlink('/tmp/bar.file.docx')

    @patch('utils.conversion.call')
    def test_docx_libreoffice_returns_none_on_errors(self, call_mock):
        """
        docx_libreoffice should return none on convert error
        """
        call_mock.return_value = 1
        ret = docx_libreoffice('/tmp/foo/bar.file.docx')
        self.assertEqual(ret, None)

    @patch('utils.conversion.call')
    def test_docx_libreoffice_returns_none_on_missed_outfile(self, call_mock):
        """
        docx_libreoffice should return none if file missed
        """
        call_mock.return_value = 0
        ret = docx_libreoffice('/tmp/foo/bar.file.doc')
        self.assertEqual(ret, None)

    @patch('utils.conversion.pdf_convert')
    @patch('utils.conversion.os.path.isfile')
    def test_pdf_to_docx_wo_ext(self, isfile_mock, pdf_convert_mock):
        """
        pdf_to_docx should return normal docxpath on file wo extension
        """
        pdf_convert_mock.return_value = True
        isfile_mock.return_value = True
        ret = pdf_to_docx('/tmp/foo/.strange_file', False)
        self.assertEqual(ret, '/tmp/foo/.strange_file.docx')

    @patch('utils.conversion.doc_convert')
    def test_doc_to_docx_wo_ext(self, call_mock):
        """
        doc_to_docx should return normal docxpath on file wo extension
        """
        call_mock.return_value = True
        ret = doc_to_docx('/tmp/foo/.strange_file')
        self.assertEqual(ret, '/tmp/foo/.strange_file.docx')

    @patch('utils.conversion.filedecode')
    @patch('utils.conversion.Document')
    def test_txt_to_docx_wo_ext(self, save_mock, call_mock):
        """
        txt_to_docx should return normal docxpath on file wo extension
        """
        call_mock.return_value = '1\n2\n3\n'
        save_mock.return_value.save.return_value = ''
        ret = txt_to_docx('/tmp/foo/.strange_file')
        self.assertEqual(ret, '/tmp/foo/.strange_file.docx')

    @patch('utils.conversion.call')
    def test_docx_to_txt_wo_ext(self, call_mock):
        """
        docx_to_txt should return normal docxpath on file wo extension
        """
        call_mock.return_value = 0
        ret = docx_to_txt('/tmp/foo/.strange_file')
        self.assertEqual(ret, '/tmp/foo/.strange_file.txt')


class CompressTest(TestCase):
    def setUp(self):
        self.files = []
        self.addCleanup(self.unlinkFiles)

    def unlinkFiles(self):
        for i in self.files:
            try:
                i.close()
            except:
                pass

    def mktemp(self, content='foo', suffix='.txt'):
        f = NamedTemporaryFile(delete=True, suffix=suffix.encode('utf-8'))
        f.write(content.encode('utf-8'))
        f.seek(0)
        self.files.append(f)

    def test_compression_works(self):
        """
        compress_to_zip should create ZIP archive with files
        """
        self.mktemp('first')
        self.mktemp('second', '.docx')
        zip = compress_to_zip(self.files)
        self.assertTrue(isinstance(zip, BytesIO))
        with ZipFile(zip, 'r') as content:
            info = content.infolist()
            self.assertEqual(len(info), 2)
            self.assertEqual(
                info[0].filename, self.files[0].name.decode('utf-8').rsplit('/')[-1])
            self.assertEqual(
                info[1].filename, self.files[1].name.decode('utf-8').rsplit('/')[-1])
            self.assertEqual(content.read(info[0].filename).decode('utf-8'), 'first')
            self.assertEqual(content.read(info[1].filename).decode('utf-8'), 'second')

    def test_compression_handles_unicode(self):
        """
        compress_to_zip should handle unicode names/content
        """
        self.mktemp('first')
        self.mktemp(u'тест', u'юникод.docx')
        zip = compress_to_zip(self.files)
        self.assertTrue(isinstance(zip, BytesIO))
        with ZipFile(zip, 'r') as content:
            info = content.infolist()
            self.assertEqual(len(info), 2)
            self.assertEqual(
                info[0].filename, self.files[0].name.decode('utf-8').rsplit('/')[-1])
            self.assertEqual(
                info[1].filename,
                self.files[1].name.decode('utf-8').rsplit('/')[-1])
            self.assertIn(u'юникод.docx', info[1].filename)
            self.assertEqual(content.read(info[0].filename).decode('utf-8'), 'first')
            self.assertEqual(content.read(info[1].filename).decode('utf-8'), 'тест')

    def test_compression_handles_missing_file(self):
        """
        compress_to_zip should skip missing files
        """
        self.mktemp('first')
        f = baker.make(File, content='unexistent.file')
        self.files.append(f.content)
        self.mktemp('second', '.docx')
        zip = compress_to_zip(self.files)
        self.assertTrue(isinstance(zip, BytesIO))
        with ZipFile(zip, 'r') as content:
            info = content.infolist()
            self.assertEqual(len(info), 2)
            self.assertEqual(
                info[0].filename, self.files[0].name.decode('utf-8').rsplit('/')[-1])
            self.assertEqual(
                info[1].filename, self.files[2].name.decode('utf-8').rsplit('/')[-1])

    def test_compression_handles_none_in_list(self):
        """
        compress_to_zip should handle 'None' in filelist (skip it)
        """
        self.mktemp('first')
        self.files.append(None)
        self.mktemp('second', '.docx')
        zip = compress_to_zip(self.files)
        self.assertTrue(isinstance(zip, BytesIO))
        with ZipFile(zip, 'r') as content:
            info = content.infolist()
            self.assertEqual(len(info), 2)
            self.assertEqual(
                info[0].filename, self.files[0].name.decode('utf-8').rsplit('/')[-1])
            self.assertEqual(
                info[1].filename, self.files[2].name.decode('utf-8').rsplit('/')[-1])


class SentenceSplittingPostProcessTests(TestCase):
    def setUp(self):
        self.api = SentenceSplittingRemoteAPI('')

    def test_post_process_on_list(self):
        """
        Should return list without containing 2+ whitespaces in a row
        """
        data = ['a b c', '  \tx  c  v', '  2  4 3', '0 9 ']
        result = self.api._post_process(data)
        self.assertEqual(['a b c', 'x c v', '2 4 3', '0 9'], result)

    def test_post_process_on_empty(self):
        """
        Should return empty list
        """
        result = self.api._post_process([])
        self.assertFalse(result)


class NameFileTests(TestCase):

    def test_get_filename_wo_ext(self):
        """
        Should return original file's name without extension
        """
        filepath = '/some/random/filename.txt'
        result = get_filename_wo_ext(filepath)
        self.assertEqual('/some/random/filename', result)

    def test_get_filename_wo_ext_on_noext(self):
        """
        Should return name if file does not have extension
        """
        filepath = '/some/random/filename'
        result = get_filename_wo_ext(filepath)
        self.assertEqual('/some/random/filename', result)

    def test_get_filename_wo_ext_dotnaming(self):
        """
        Should return name of file has dot in the name's beginging
        """
        filepath = '/some/random/.filename'
        result = get_filename_wo_ext(filepath)
        self.assertEqual('/some/random/.filename', result)

    def test_get_filename_wo_ext_dotnaming_with_ext(self):
        """
        Should return name of file has dot in the name's beginging
        """
        filepath = '/some/random/.filename.txt'
        result = get_filename_wo_ext(filepath)
        self.assertEqual('/some/random/.filename', result)


class PersonalDataTest(TestCase):

    def setUp(self):
        with zipfile.ZipFile(os.path.join(
                os.path.dirname(__file__),
                'data',
                'test',
                'Contract.docx'
        ), mode='r') as zin:
            self.doc = zin.read('word/document.xml')

        with zipfile.ZipFile(os.path.join(
                os.path.dirname(__file__),
                'data',
                'test',
                'Contract obf text.docx'
        ), mode='r') as zin:
            self.obf_text = zin.read('word/document.xml')

        with zipfile.ZipFile(os.path.join(
                os.path.dirname(__file__),
                'data',
                'test',
                'Contract highlight.docx'
        ), mode='r') as zin:
            self.highlight = zin.read('word/document.xml')

        with zipfile.ZipFile(os.path.join(
                os.path.dirname(__file__),
                'data',
                'test',
                'Contract obf sents.docx'
        ), mode='r') as zin:
            self.obf_sents = zin.read('word/document.xml')

    def test_gather_by_regex(self):
        text = open(os.path.join(
            os.path.dirname(__file__),
            'data', 'test', 'rgx.txt')
        , encoding='utf-8').read()

        result = sorted(personal_data.gather_by_regex(text))

        self.assertEqual([
            ('American Express Card', '3481-686298-29108', 'Text: 1087:1104'),
            ('American Express Card', '3776 168745 03335', 'Text: 1106:1123'),
            ('BankCard', '5610 5158 7631 8134', 'Text: 1659:1678'),
            ('Canada Social Insurance Number', '123 456 789', 'Text: 451:462'),
            ('Canada Social Insurance Number', '123-456-789', 'Text: 438:449'),
            ('Dankort Card', '5019-5622-7188-4877', 'Text: 1590:1609'),
            ('Date', '18.04.2018', 'Text: 68:78'),
            ('Date', 'April 18th 2018', 'Text: 80:95'),
            ('Diners Club Carte Blanche Card', '3019-326199-1431', 'Text: 1884:1900'),
            ('Diners Club Carte Blanche Card', '30483 4501 21175', 'Text: 1902:1918'),
            ('Diners Club International Card', '3019-326199-1431', 'Text: 1884:1900'),
            ('Diners Club International Card', '30483 4501 21175', 'Text: 1902:1918'),
            ('Diners Club International Card', '30948 8332 62722', 'Text: 2013:2029'),
            ('Diners Club International Card', '3622-280211-7273', 'Text: 2052:2068'),
            ('Diners Club International Card', '38177-7864-7560836', 'Text: 2070:2088'),
            ('Diners Club International Card', '3955-6132-6838-7263', 'Text: 2031:2050'),
            ('Diners Club enRoute Card', '2014-1156182-1956', 'Text: 1833:1850'),
            ('Diners Club enRoute Card', '21497 4364 608826', 'Text: 1814:1831'),
            ('Email', 'vitarcheg@gmail.com', 'Text: 215:234'),
            #('Greece National ID Card Number', 'EX-123456', 'Text: 863:872'),
            #('Greece National ID Card Number', 'Ψ-123456', 'Text: 896:904'),
            ('Hong Kong Identity Card Number', 'AB123456(7)', 'Text: 779:790'),
            ('International Banking Account Number', 'AT61 19043002 34573201', 'Text: 704:726'),
            ('International Banking Account Number', 'DE89 3704 0044 0532 0130 00', 'Text: 675:702'),
            ('International Banking Account Number', 'NL91ABNA0417164300', 'Text: 728:746'),
            ('JCB Card', '3553 2883 7290 3563', 'Text: 1135:1154'),
            ('JCB Card', '3585-9068-8405-2825', 'Text: 1156:1175'),
            ('Laser Card', '6709-8290-3555-4982', 'Text: 1729:1748'),
            ('Link', 'http://beagle.ai', 'Text: 163:179'),
            ('Maestro Card', '5016-175225-08531', 'Text: 1265:1282'),
            ('Maestro Card', '5019-5622-7188-4877', 'Text: 1590:1609'),
            ('Maestro Card', '5610 5158 7631 8134', 'Text: 1659:1678'),
            ('Maestro Card', '5624 7078 1043 8841', 'Text: 1244:1263'),
            ('Maestro Card', '6130 2381 78175', 'Text: 1284:1299'),
            ('Maestro Card', '6277 9474 4969 6355', 'Text: 1359:1378'),
            ('Maestro Card', '6709-8290-3555-4982', 'Text: 1729:1748'),
            ('Maestro Card', '6848-8343-5650-5540', 'Text: 1301:1320'),
            ('Malaysia ID Card Number', '930201-69-1239', 'Text: 816:830'),
            ('MasterCard', '5221-2213-3844-0302', 'Text: 1451:1470'),
            ('MasterCard', '5382 8038 4332 0171', 'Text: 1430:1449'),
            ('Phone', '+38 (093) 566-02-69', 'Text: 978:997'),
            ('Phone', '+38(093)566-0269', 'Text: 943:959'),
            ('Phone', '+380935660269', 'Text: 114:127'),
            #('Price', '$50000', 'Text: 253:259'),
            #('Price', '50000$', 'Text: 261:267'),
            ('Salutation', 'Miss', 'Text: 537:541'),
            ('Salutation', 'Mr', 'Text: 524:526'),
            ('Salutation', 'Mrs.', 'Text: 566:570'),
            ('Salutation', 'Ms.', 'Text: 552:555'),
            ('Sexual Orientation', 'Homosexual', 'Text: 303:313'),
            ('UATP Card', '141-5383-7463-2874', 'Text: 1483:1501'),
            ('UATP Card', '1522 28313 708748', 'Text: 1503:1520'),
            ('UK National Insurance Number', 'AB 12 34 56 A', 'Text: 370:383'),
            ('UK National Insurance Number', 'AB-12-34-56-A', 'Text: 385:398'),
            ('USA Social Security Number', '078-05-1121', 'Text: 511:522'),
            ('USA Social Security Number', '219 09 9998', 'Text: 498:509'),
            ('UnionPay Card', '624643-2813460546945', 'Text: 1337:1357'),
            ('UnionPay Card', '6277 9474 4969 6355', 'Text: 1359:1378'),
            ('Visa Card', '4539 3179 4697 6842', 'Text: 1209:1228'),
            ('Visa Card', '4929-9546-5622-0801', 'Text: 1188:1207'),
            ('Voyager Card', '8699 4454 5832 023', 'Text: 1536:1554'),
            ('Voyager Card', '8699-7066-8364-080', 'Text: 1556:1574'),
        ], result)

    def test_gather_by_spacy(self):
        text = open(os.path.join(
            os.path.dirname(__file__),
            'data', 'test',
            'Contract.txt')
        ,'r' , encoding='utf-8').read()

        result = sorted(personal_data.gather_by_spacy(text))

        self.assertEqual([
            ('Location', u'California', 'Text: 57975:57985'),
            ('Location', u'Delaware', 'Text: 2160:2168'),
            ('Location', u'Florida', 'Text: 2035:2042'),
            ('Location', u'NV', 'Text: 310:312'),
            ('Location', u'NY', 'Text: 4566:4568'),
            ('Location', u'New York', 'Text: 4556:4564'),
            ('Location', u'Orange County', 'Text: 58215:58228'),
            ('Location', u'Palm Beach', 'Text: 55854:55864'),
            ('Location', u'State of California', 'Text: 57966:57985'),
            ('Location', u'United States', 'Text: 3783:3796'),
            ('Location', u'United States of America', 'Text: 3783:3807'),
            ('Person', u'3871 S. Valley View Blvd', 'Text: 54421:54445'),
            ('Person', u'By:/s/ Richard Davis', 'Text: 66953:66973'),
            ('Person', u'Esq', 'Text: 55510:55513'),
            ('Person', u'Las Vegas', 'Text: 54549:54558'),
            ('Person', u'Laura Anthony', 'Text: 55495:55508'),
            ('Person', u'Richard Davis', 'Text: 66960:66973'),
            ('Person', u'e', 'Text: 1221:1222'),
            ('Person', u'e-mail', 'Text: 9265:9271'),
        ], result)

    def test_obfuscate_text(self):
        replacements = [
            ('shareholder@brkincorporated.com', 'text', 'string'),
            ('LAnthony@LegalandCompliance.com', 'text', 'string'),
            ('investments@kodiakfunds.com', 'text', 'string'),
            ('United States of America', 'text', 'string'),
            ('3871 S. Valley View Blvd', 'text', 'string'),
            ('Ryan@KodiakFunds.com', 'text', 'string'),
            ('By:/s/ Richard Davis', 'text', 'string'),
            ('State of California', 'text', 'string'),
            ('West Palm Beach', 'text', 'string'),
            ('www.Nasdaq.com', 'text', 'string'),
            ('United States', 'text', 'string'),
            ('Newport Beach', 'text', 'string'),
            ('Laura Anthony', 'text', 'string'),
            ('Orange County', 'text', 'string'),
            ('Richard Davis', 'text', 'string'),
            ('May 15, 2017', 'text', 'string'),
            ('$37,500.00', 'text', 'string'),
            ('$33,750.00', 'text', 'string'),
            ('$20,000.00', 'text', 'string'),
            ('California', 'text', 'string'),
            ('$3,750.00', 'text', 'string'),
            ('Las Vegas', 'text', 'string'),
            ('Delaware', 'text', 'string'),
            ('New York', 'text', 'string'),
            ('$33,750', 'text', 'string'),
            ('$500.00', 'text', 'string'),
            ('$75,000', 'text', 'string'),
            ('$0.0001', 'text', 'string'),
            ('Florida', 'text', 'string'),
            ('$2,000', 'text', 'string'),
            ('setoff', 'text', 'string'),
            ('FAST', 'text', 'string'),
            ('Esq', 'text', 'string'),
            ('NY', 'text', 'string'),
            ('NV', 'text', 'string')]

        result = personal_data.obfuscate_text('[[CONFIDENTIAL]]', self.doc, replacements)

        self.assertEqual(self.obf_text, result)

    def test_highlight_text(self):
        replacements = [
            ('shareholder@brkincorporated.com', 'text', 'highlight'),
            ('LAnthony@LegalandCompliance.com', 'text', 'highlight'),
            ('investments@kodiakfunds.com', 'text', 'highlight'),
            ('United States of America', 'text', 'highlight'),
            ('3871 S. Valley View Blvd', 'text', 'highlight'),
            ('Ryan@KodiakFunds.com', 'text', 'highlight'),
            ('By:/s/ Richard Davis', 'text', 'highlight'),
            ('State of California', 'text', 'highlight'),
            ('West Palm Beach', 'text', 'highlight'),
            ('www.Nasdaq.com', 'text', 'highlight'),
            ('United States', 'text', 'highlight'),
            ('Newport Beach', 'text', 'highlight'),
            ('Laura Anthony', 'text', 'highlight'),
            ('Orange County', 'text', 'highlight'),
            ('Richard Davis', 'text', 'highlight'),
            ('May 15, 2017', 'text', 'highlight'),
            ('$37,500.00', 'text', 'highlight'),
            ('$33,750.00', 'text', 'highlight'),
            ('$20,000.00', 'text', 'highlight'),
            ('California', 'text', 'highlight'),
            ('$3,750.00', 'text', 'highlight'),
            ('Las Vegas', 'text', 'highlight'),
            ('Delaware', 'text', 'highlight'),
            ('New York', 'text', 'highlight'),
            ('$33,750', 'text', 'highlight'),
            ('$500.00', 'text', 'highlight'),
            ('$75,000', 'text', 'highlight'),
            ('$0.0001', 'text', 'highlight'),
            ('Florida', 'text', 'highlight'),
            ('$2,000', 'text', 'highlight'),
            ('setoff', 'text', 'highlight'),
            ('FAST', 'text', 'highlight'),
            ('Esq', 'text', 'highlight'),
            ('NY', 'text', 'highlight'),
            ('NV', 'text', 'highlight')]

        result = personal_data.highlight_text('red', self.doc, replacements)

        self.assertEqual(self.highlight, result)

    def test_obfuscate_sents(self):
        sents = [
            ('This Note may not be prepaid in whole or in part except as otherwise explicitly set forth herein.', 'string'),
            ('Thus, the purchase price of this Note shall be $37,500.00, computed as follows: the Principal Amount minus the OID.', 'highlight')
        ]

        result = personal_data.obfuscate_sents('[[CONFIDENTIAL]]', 'red', self.doc, sents)
        print(self.obf_sents.decode('utf-8'), result.decode('utf-8'))
        self.assertEqual(self.obf_sents, result)
