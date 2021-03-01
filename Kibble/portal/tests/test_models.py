import os
import zipfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import patch
from model_mommy import mommy, recipe

from document.models import Document, Sentence
from document.tests.helpers import side_effect_tmpfile, TempCleanupTestCase, \
    temp_names, side_effect_tmp
from portal.constants import ProjectStatus
from portal.models import File, Batch, Project, ProjectArchive
from shared.mixins import PatcherMixin

filerecipe = recipe.Recipe(
    File,
    content=recipe.seq('mock.file')
)


class ModelTest(TempCleanupTestCase):
    def setUp(self):
        self.seq = range(10)

    def make_file(self):
        id = self.seq.pop()
        return SimpleUploadedFile('test%d.docx' % id, b'Test Content')

    def get_test_file(self, name):
        img = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', name
        )
        with open(img, 'rb') as f:
            suf = SimpleUploadedFile(name, f.read(), None)
        return suf

    def test_project_model_exists(self):
        """
        Project model should have name, status and optional user FK
        """
        project = mommy.make(Project, name='Foo')
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, 'Foo')
        self.assertEqual(project.owner, None)
        user = mommy.make(User)
        project.owner = user
        project.save()
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.owner, user)
        with self.assertRaises(Exception):
            Project.objects.create(name=None)

    def test_batch_model_has_project_field(self):
        """
        Batch model should have optional project m2m
        """
        project = mommy.make(Project)
        batch = mommy.make(Batch)
        self.assertEqual(batch.project.count(), 0)
        batch.project.add(project)
        batch.save()
        batch = Batch.objects.get(pk=batch.pk)
        self.assertEqual(batch.project.all()[0], project)
        batch.project.add(mommy.make(Project))
        self.assertEqual(batch.project.count(), 2)

    @patch('portal.models.File.get_type')
    def test_file_model_has_type_field(self, gettype_mock):
        """
        File model should have type field (None by default)
        """
        gettype_mock.return_value = None
        obj = mommy.make(File)
        self.assertIsNone(obj.type)

    def test_save_file_in_correct_dir(self):
        """
        Should save under uploads/<batch_id>_<project_name>
        """
        batch = mommy.make(Batch, name='Bar')
        batch = Batch.objects.get(pk=batch.pk)

        file_ = mommy.make(File, content=self.make_file(), batch=batch)
        file_ = File.objects.get(pk=file_.pk)

        expected_par_dir = '{}_{}'.format(
            batch.id, batch.name.replace(' ', '_')
        )

        self.assertEqual(
            expected_par_dir,
            file_.content.name.split(os.path.sep)[-2]
        )

    def test_convert_img_to_pdf(self):
        """
        Convert and replace an image to pdf
        """
        suf = self.get_test_file('scansmpl.png')
        batch = mommy.make(Batch)
        file_ = mommy.make(File, content=suf, batch=batch)
        old_content = file_.content
        file_.img2pdf()
        self.assertRaises(Exception, lambda: old_content.size)
        self.assertTrue(file_.content.size)
        self.assertTrue(file_.content.name.endswith('pdf'))

    @patch('utils.personal_data.find_personal_data')
    @patch('document.models.docx_to_txt')
    @patch('portal.models.compress_to_zip')
    def test_get_compressed_docx_files(
            self, compress_mock, convert_mock, personal_data_mock):
        """
        Should get all converted DOCX files in zip file
        """
        convert_mock.side_effect = side_effect_tmpfile
        compress_mock.return_value = 'Fooo'
        batch = mommy.make(Batch)
        file1 = mommy.make(File, content=self.make_file(), batch=batch)
        file1.convert()
        file2 = mommy.make(File, content=self.make_file(), batch=batch)
        file2.convert()
        batch2 = mommy.make(Batch)
        file3 = mommy.make(File, content=self.make_file(), batch=batch2)
        file3.convert()

        docs = Document.objects.filter(source_file__batch=batch)
        ret = batch.get_converted_documents(False)
        self.assertEqual(ret, 'Fooo')
        filelist = [i.content_file for i in docs]
        compress_mock.assert_called_once_with(filelist)

    @patch('utils.personal_data.find_personal_data')
    @patch('document.models.docx_to_txt')
    @patch('portal.models.compress_to_zip')
    def test_get_compressed_txt_files(
            self, compress_mock, convert_mock, personal_data_mock):
        """
        Should get all converted txt files in zip file
        """
        convert_mock.side_effect = side_effect_tmpfile
        compress_mock.return_value = 'Fooo'
        batch = mommy.make(Batch)
        file1 = mommy.make(File, content=self.make_file(), batch=batch)
        file1.convert()
        file2 = mommy.make(File, content=self.make_file(), batch=batch)
        file2.convert()
        batch2 = mommy.make(Batch)
        file3 = mommy.make(File, content=self.make_file(), batch=batch2)
        file3.convert()

        docs = Document.objects.filter(source_file__batch=batch)
        ret = batch.get_converted_documents(True)
        self.assertEqual(ret, 'Fooo')
        filelist = [i.text_file for i in docs]
        compress_mock.assert_called_once_with(filelist)

    @patch('utils.personal_data.find_personal_data')
    @patch('document.models.docx_to_txt')
    @patch('portal.models.compress_to_zip')
    def test_get_compressed_files_handle_empty_field(
            self, compress_mock, convert_mock, personal_data_mock):
        """
        Should get all converted txt files in zip file
        """
        convert_mock.side_effect = side_effect_tmpfile
        compress_mock.return_value = 'Fooo'
        batch = mommy.make(Batch)
        file1 = mommy.make(File, content=self.make_file(), batch=batch)
        file1.convert()
        file2 = mommy.make(File, content=self.make_file(), batch=batch)
        file2.convert()
        obj = Document.objects.last()
        obj.content_file = None
        obj.text_file = None
        obj.save()

        ret = batch.get_converted_documents(True)
        self.assertEqual(ret, 'Fooo')
        filelist = [Document.objects.first().text_file, None]
        compress_mock.assert_called_once_with(filelist)
        compress_mock.reset_mock()

        ret = batch.get_converted_documents(False)
        self.assertEqual(ret, 'Fooo')
        filelist = [Document.objects.first().content_file, None]
        compress_mock.assert_called_once_with(filelist)

    def test_file_is_deleted_on_instance_deletion(self):
        """
        Files in media should be deleted on instance deletion
        """
        batch = mommy.make(Batch, name='Bar')
        file_ = mommy.make(File, content=self.make_file(), batch=batch)
        content = file_.content
        self.assertTrue(content.size)
        file_.delete()
        self.assertRaises(Exception, lambda: content.size)

    def test_file_is_deleted_on_queryset_deletion(self):
        """
        Files in media should be deleted on file queryset deletion
        """
        batch = mommy.make(Batch, name='Bar')
        file_ = mommy.make(File, content=self.make_file(), batch=batch)
        content = file_.content
        self.assertTrue(content.size)
        File.objects.filter(pk=file_.pk).delete()
        self.assertRaises(Exception, lambda: content.size)

    def test_file_is_deleted_on_batch_instance_deletion(self):
        """
        Files in media should be deleted on instance deletion
        """
        batch = mommy.make(Batch, name='Bar')
        file_ = mommy.make(File, content=self.make_file(), batch=batch)
        self.assertTrue(file_.content.size)
        batch.delete()
        self.assertRaises(Exception, lambda: file_.content.size)

    def test_file_is_deleted_on_batch_queryset_deletion(self):
        """
        Files in media should be deleted on file queryset deletion
        """
        batch = mommy.make(Batch, name='Bar')
        file_ = mommy.make(File, content=self.make_file(), batch=batch)
        self.assertTrue(file_.content.size)
        Batch.objects.filter(pk=batch.pk).delete()
        self.assertRaises(Exception, lambda: file_.content.size)

    def test_file_can_have_null_batch(self):
        """
        File object can have None value in batch field
        """
        fileobj = mommy.make(File, batch=None)
        self.assertTrue(fileobj.batch is None)

    @patch('portal.models.File.check_zipped_type')
    @patch('magic.from_buffer')
    def test_file_type_check(self, magic_mock, zip_type_mock):
        """
        Check that file type is set correct
        """
        zip_type_mock.return_value = File.FILE_ZIP
        fileobj = mommy.make(
            File, content=SimpleUploadedFile('foo', b'foobar'))
        for mime, type in File.FILE_TYPES:
            magic_mock.reset_mock()
            # skip REGEX mime check
            if hasattr(mime, 'pattern'):
                continue
            magic_mock.return_value = mime
            self.assertEqual(fileobj.get_type(), type)
            magic_mock.assert_called_once_with(b'foobar', mime=True)

    @patch('magic.from_buffer')
    def test_file_type_check_regex(self, magic_mock):
        """
        Check that file type is set correct for regex cases
        """
        fileobj = mommy.make(
            File, content=SimpleUploadedFile('foo', b'foobar'))
        magic_mock.reset_mock()
        magic_mock.return_value = 'text/x-foobar'
        self.assertEqual(fileobj.get_type(), File.FILE_TXT)
        magic_mock.assert_called_once_with(b'foobar', mime=True)

    @patch('magic.from_buffer')
    def test_file_type_unknown(self, magic_mack):
        """
        File type for unknown mime is FILE_UNKNOWN
        """
        fileobj = mommy.make(File, content=SimpleUploadedFile('foo', b'moo'))
        magic_mack.reset_mock()
        magic_mack.return_value = 'Foo'
        self.assertEqual(fileobj.get_type(), File.FILE_UNKNOWN)
        magic_mack.assert_called_once_with(b'moo', mime=True)

    @patch('portal.models.File.get_type')
    def test_file_type_check_on_save(self, gettype_mock):
        """
        Check that file type is set correct
        """
        gettype_mock.return_value = File.FILE_DOC
        fileobj = mommy.make(File)
        gettype_mock.assert_called_once()
        self.assertEqual(fileobj.type, File.FILE_DOC)

    @patch('portal.models.File.get_type')
    def test_file_type_dont_check_if_set(self, gettype_mock):
        """
        Do not check type if it is set
        """
        gettype_mock.return_value = File.FILE_DOC
        fileobj = mommy.make(File, type=File.FILE_UNKNOWN)
        gettype_mock.assert_not_called()
        self.assertEqual(fileobj.type, File.FILE_UNKNOWN)

    def test_broken_docx_detected_correctly(self):
        """
        Broken docx detected as docx, not as zip
        """
        suf = self.get_test_file(
            '654441804_2_Westpac - Confidentiality deed - two way.docx')
        File.objects.create(content=suf)
        self.assertEqual(File.objects.count(), 1)
        file = File.objects.first()
        self.assertEqual(file.type, File.FILE_DOCX)

    def test_docx_like_detected_correctly(self):
        """
        zip with word/document.xml detected as docx, not as zip
        """
        suf = self.get_test_file('bad.docx')
        File.objects.create(content=suf)
        self.assertEqual(File.objects.count(), 1)
        file = File.objects.first()
        self.assertEqual(file.type, File.FILE_DOCX)

    def test_txt_detected_correctly(self):
        """
        txt file with long lines detected correctly
        """
        suf = self.get_test_file(
            '-donnell-strategic-industrial-reit-inc-1503993-2012-11-14')
        File.objects.create(content=suf)
        self.assertEqual(File.objects.count(), 1)
        file = File.objects.first()
        self.assertEqual(file.type, File.FILE_TXT)


class FileConvertTest(TempCleanupTestCase, PatcherMixin):
    def setUp(self):
        self.patch('document.models', 'docx_to_txt')
        self.docx_to_txt.return_value = None
        self.patch('portal.models', 'pdf_to_docx')
        self.patch('portal.models', 'txt_to_docx')
        self.patch('portal.models', 'doc_to_docx')
        self.patch('portal.models', 'requires_ocr')
        self.patch('os', 'remove')
        self.patch('portal.models', 'open')
        self.patch('portal.models.File', 'get_content_file')
        self.get_content_file.side_effect = side_effect_tmp
        self.open.return_value.read.return_value = 'test'

    def make_file(self):
        return SimpleUploadedFile('test', b'Test Content')

    def get_name(self, path):
        return os.path.basename(path)

    @patch('utils.personal_data.find_personal_data')
    def test_text_file_convert(self, personal_data_mock):
        """
        Should convert text file to docx
        """
        content = mommy.make(
            File, type=File.FILE_TXT, content=self.make_file())
        self.txt_to_docx.side_effect = side_effect_tmpfile
        content.convert()
        self.txt_to_docx.assert_called_once_with(temp_names[0])
        self.doc_to_docx.assert_not_called()
        self.pdf_to_docx.assert_not_called()
        self.requires_ocr.assert_not_called()
        d = Document.objects.first()
        self.assertTrue(d)
        self.assertEqual(d.source_file, content)
        self.assertIn(d.name, self.get_name(content.content.name))

    @patch('utils.personal_data.find_personal_data')
    def test_doc_file_convert(self, personal_data_mock):
        """
        Should convert doc file to docx
        """
        content = mommy.make(
            File, type=File.FILE_DOC, content=self.make_file())
        self.doc_to_docx.side_effect = side_effect_tmpfile
        content.convert()
        self.doc_to_docx.assert_called_once_with(temp_names[0])
        self.txt_to_docx.assert_not_called()
        self.pdf_to_docx.assert_not_called()
        self.requires_ocr.assert_not_called()
        d = Document.objects.first()
        self.assertTrue(d)
        self.assertIn(d.name, self.get_name(content.content.name))
        self.assertEqual(d.source_file, content)

    @patch('utils.personal_data.find_personal_data')
    def test_pdf_file_convert(self, personal_data_mock):
        """
        Should convert pdf file to docx
        """
        self.requires_ocr.return_value = False
        content = mommy.make(
            File, type=File.FILE_PDF, content=self.make_file())
        self.pdf_to_docx.side_effect = side_effect_tmpfile
        content.convert()
        self.pdf_to_docx.assert_called_once_with(temp_names[0], False)
        self.txt_to_docx.assert_not_called()
        self.doc_to_docx.assert_not_called()
        self.requires_ocr.assert_called()
        d = Document.objects.first()
        self.assertTrue(d)
        self.assertIn(d.name, self.get_name(content.content.name))
        self.assertEqual(d.source_file, content)

    @patch('utils.personal_data.find_personal_data')
    def test_docx_file_convert(self, personal_data_mock):
        """
        Should convert docx file to docx - just create Document and do nothing
        """
        content = mommy.make(
            File, type=File.FILE_DOCX, content=self.make_file())
        content.convert()
        self.pdf_to_docx.assert_not_called()
        self.txt_to_docx.assert_not_called()
        self.doc_to_docx.assert_not_called()
        self.requires_ocr.assert_not_called()
        self.remove.assert_not_called()
        d = Document.objects.first()
        self.assertTrue(d)
        self.assertEqual(d.name, self.get_name(content.content.name))
        self.assertEqual(d.source_file, content)

    @patch('utils.personal_data.find_personal_data')
    def test_file_convert_returns_document(self, personal_data_mock):
        """
        Should return document on convert finish
        """
        content = mommy.make(
            File, type=File.FILE_DOCX, content=self.make_file())
        doc = content.convert()
        d = Document.objects.first()
        self.assertTrue(d)
        self.assertEqual(d, doc)

    @patch('portal.models.File.get_type')
    def test_file_convert_returns_none_on_error(self, gettype_mock):
        """
        Should return None on convert error
        """
        gettype_mock.return_value = File.FILE_UNKNOWN
        content = mommy.make(
            File, type=File.FILE_UNKNOWN, content=self.make_file())
        doc = content.convert()
        d = Document.objects.first()
        self.assertFalse(d)
        self.assertFalse(doc)

    def test_set_need_ocr_to_true_on_save(self):
        """
        If file is a candidate to be ocred (like non, doc, txt) then check
        is it requires ocring and set right prop
        """
        self.requires_ocr.return_value = True
        file = mommy.make(
            File, type=File.FILE_PDF, content=self.make_file())
        self.requires_ocr.assert_called()
        self.assertTrue(file.need_ocr)

    def test_set_need_ocr_to_false_on_save(self):
        """
        If file is a candidate to be ocred (like non, doc, txt) then check
        is it requires ocring and set right prop
        """
        self.requires_ocr.return_value = False
        file = mommy.make(
            File, type=File.FILE_TXT, content=self.make_file())
        self.requires_ocr.assert_not_called()
        self.assertFalse(file.need_ocr)

    @patch('utils.personal_data.find_personal_data')
    @patch('portal.models.File.get_type')
    def test_file_convert_recalls_gettype_on_unknown_type(
            self, gettype_mock, personal_data_mock):
        """
        If file type is None or unknown - re-call get_type()
        """
        gettype_mock.return_value = File.FILE_DOCX
        content = mommy.make(
            File, type=File.FILE_UNKNOWN, content=self.make_file())
        doc = content.convert()
        gettype_mock.assert_called_once()
        self.assertTrue(doc)
        self.assertTrue(Document.objects.exists())

        # None case
        Document.objects.all().delete()
        content.type = None
        gettype_mock.reset_mock()
        doc = content.convert()
        gettype_mock.assert_called_once()
        self.assertTrue(doc)
        self.assertTrue(Document.objects.exists())


class ProjectTest(TestCase):

    def make_dataset(self):
        self.empty_project = mommy.make(Project, name='empty')
        self.project = mommy.make(Project, name='project')
        self.batch1 = mommy.make(Batch, name='batch1', project=[self.project])
        self.batch2 = mommy.make(Batch, name='batch2', project=[self.project])
        self.id = 0
        self.files1 = [
            mommy.make(File, batch=self.batch1, content=self.make_file)
            for i in range(3)
        ]
        self.files2 = [
            mommy.make(File, batch=self.batch2, content=self.make_file)
            for i in range(3)
        ]

    def make_file(self):
        self.id += 1
        return SimpleUploadedFile('test%d.docx' % self.id, b'Test Content')

    def get_zip_structure(self, project):
        ret = []
        for batch in project.batches.all():
            dirname = '%s_%s/' % (batch.id, batch.name)
            for file in batch.files.all():
                ret.append(dirname + file.content.name)
        return ret

    def test_compress_project_returns_instance(self):
        """
        Compress project returns ArchiveProject instance
        """
        self.make_dataset()
        archive = self.project.compress()
        self.assertIsInstance(archive, ProjectArchive)
        self.assertTrue(self.project.archive.content_file.size)

    def test_compress_empty_project(self):
        """
        Do not compress but change status
        """
        self.make_dataset()
        archive = self.empty_project.compress()
        self.assertIsInstance(archive, ProjectArchive)
        self.assertFalse(hasattr(archive.content_file, 'url'))
        self.assertEqual(self.empty_project.status, ProjectStatus.Archived.value)

    def test_create_archive(self):
        """
        Right archive structure
        """
        self.make_dataset()
        archive = self.project.compress()
        zipped = zipfile.ZipFile(archive.content_file)
        self.assertIn('%s_%s' % (self.project.id, self.project.name), zipped.filename)
        expected_namelist = ['{0.id}_{0.name}.zip'.format(b) for b in self.project.batches.all()]
        self.assertEqual(sorted(expected_namelist), sorted(zipped.namelist()))

    def test_change_project_status(self):
        """
        If a project has an archive then project is Inactive
        """
        self.make_dataset()
        self.assertEqual(self.project.status, ProjectStatus.Active.value)
        self.project.compress()
        self.assertEqual(self.project.status, ProjectStatus.Archived.value)

    def test_update_archive(self):
        """
        Update archive
        """
        self.make_dataset()
        archive = self.project.compress()
        first_timestamp = archive.created_at
        archive = self.project.compress()
        second_timestamp = archive.created_at
        self.assertGreater(second_timestamp, first_timestamp)

    def test_project_name_unique(self):
        """
        Unique project name is required
        """
        mommy.make(Project, name='project')
        with self.assertRaises(Exception):
            mommy.make(Project, name='project')


class BatchTest(TestCase):
    def make_dataset(self):
        self.batches = mommy.make(Batch, 3)
        self.id = 0
        self.files_b0 = [
            mommy.make(File, batch=self.batches[0], content=self.make_file)
            for i in range(3)
        ]
        self.files_b1 = [
            mommy.make(File, batch=self.batches[1], content=self.make_file)
            for i in range(3)
        ]
        self.doc_f0 = mommy.make(Document, 3, source_file=self.files_b0[0])
        self.doc_f1 = mommy.make(Document, 3, source_file=self.files_b0[1])
        self.doc_f2 = mommy.make(Document, 3, source_file=self.files_b0[2])
        mommy.make(Sentence, 4, document=self.doc_f1[1])
        mommy.make(Sentence, 2, document=self.doc_f2[2])
        self.doc_b1_f1 = mommy.make(Document, 3, source_file=self.files_b1[1])
        mommy.make(Sentence, 11, document=self.doc_b1_f1[1])

    def make_file(self):
        self.id += 1
        return SimpleUploadedFile('test%d.docx' % self.id, b'Test Content')

    def test_get_zipped_files(self):
        """
        Returns filelike object, compressed files
        """
        self.make_dataset()
        filelike = self.batches[0].get_zipped_files()
        zipped = zipfile.ZipFile(filelike)
        self.assertEqual(len(zipped.namelist()), 3)
        expected_namelist = [f.filename for f in self.files_b0]
        self.assertEqual(sorted(zipped.namelist()), sorted(expected_namelist))

    def test_get_sentences_count(self):
        """
        All sentences belongs to batch documents should be calculated
        """
        self.make_dataset()
        self.assertEqual(self.batches[0].sentences_count, 6)
        self.assertEqual(self.batches[1].sentences_count, 11)
        self.assertEqual(self.batches[2].sentences_count, 0)
