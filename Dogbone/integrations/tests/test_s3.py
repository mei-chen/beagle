from StringIO import StringIO

from django.conf import settings
from django.test import TestCase
import mock


from integrations.s3 import get_s3_bucket_manager, S3ResponseError, ssl_s3url


class S3BaseMock(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        return type(self) == type(other) and \
               self.args == other.args and \
               self.kwargs == other.kwargs


class S3ConnectionMock(S3BaseMock):

    def get_bucket(self, *args, **kwargs):
        return S3BucketMock(*args, **kwargs)

    def create_bucket(self, *args, **kwargs):
        return S3BucketMock(*args, **kwargs)


def cannot_get_bucket_mock(*args, **kwargs):
    raise S3ResponseError(404, 'NoSuchBucket',
                          'The specified bucket does not exist')


class S3BucketMock(S3BaseMock):
    pass


class S3KeyMock(S3BaseMock):

    # Placeholder methods which will be mocked (but must be present anyway!)

    def delete(self):
        pass

    def set_contents_from_string(self, string):
        pass

    def get_contents_as_string(self):
        pass

    def set_contents_from_filename(self, file_path):
        pass

    def get_contents_to_filename(self, file_path):
        pass

    def set_contents_from_file(self, file_handle):
        pass

    def get_contents_to_file(self, file_handle):
        pass

    def set_metadata(self, metadata_key, metadata_value):
        pass

    def get_metadata(self, metadata_key):
        pass


class S3Test(TestCase):

    def setUp(self):
        super(S3Test, self).setUp()

        self.connection_patcher = mock.patch('integrations.s3.S3Connection',
                                             side_effect=S3ConnectionMock)
        self.connection_mock = self.connection_patcher.start()

        self.key_patcher = mock.patch('integrations.s3.Key',
                                      side_effect=S3KeyMock)
        self.key_mock = self.key_patcher.start()

        self.bucket_name = 'bucket'
        self.bucket_naming_template = 'test_%s'

        self.key_name = 'key'

        self.string = 'string'
        self.file_path = 'filename'
        self.file_handle = StringIO()
        self.metadata_key = 'metadata_key'
        self.metadata_value = 'metadata_value'

    def create_manager(self):
        return get_s3_bucket_manager(self.bucket_name,
                                     self.bucket_naming_template)

    def check_manager(self, manager):
        self.assertEqual(manager.ACCESS_KEY_ID,
                         settings.AWS_ACCESS_KEY_ID)
        self.assertEqual(manager.SECRET_ACCESS_KEY,
                         settings.AWS_SECRET_ACCESS_KEY)
        self.assertEqual(manager.BUCKET_NAME,
                         self.bucket_naming_template % self.bucket_name)
        self.assertEqual(manager.bucket,
                         S3BucketMock(manager.BUCKET_NAME))
        self.connection_mock.assert_called_once_with(manager.ACCESS_KEY_ID,
                                                     manager.SECRET_ACCESS_KEY,
                                                     calling_format=mock.ANY)

    def test_s3_manager_get_old_bucket(self):
        manager = self.create_manager()
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3ConnectionMock.get_bucket',
                side_effect=cannot_get_bucket_mock)
    def test_s3_manager_create_new_bucket(self, get_bucket_mock):
        manager = self.create_manager()
        get_bucket_mock.assert_called_once_with(manager.BUCKET_NAME)
        self.check_manager(manager)

    def test_s3_manager_build_key(self):
        manager = self.create_manager()
        key = manager.build_key(self.key_name)
        self.assertEqual(key.key, self.key_name)
        self.assertEqual(key, S3KeyMock(manager.bucket))
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.delete')
    def test_s3_manager_delete_key(self, delete_mock):
        manager = self.create_manager()
        manager.delete_key(self.key_name)
        delete_mock.assert_called_once_with()
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.set_contents_from_string')
    def test_s3_manager_save_string(self, set_contents_from_string_mock):
        manager = self.create_manager()
        manager.save_string(self.key_name, self.string)
        set_contents_from_string_mock.assert_called_once_with(self.string)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.get_contents_as_string')
    def test_s3_manager_read_to_string(self, get_contents_as_string_mock):
        manager = self.create_manager()
        manager.read_to_string(self.key_name)
        get_contents_as_string_mock.assert_called_once_with()
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.set_contents_from_filename')
    def test_s3_manager_save_filename(self, set_contents_from_filename_mock):
        manager = self.create_manager()
        manager.save_filename(self.key_name, self.file_path)
        set_contents_from_filename_mock.assert_called_once_with(self.file_path)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.get_contents_to_filename')
    def test_s3_manager_read_to_filename(self, get_contents_to_filename_mock):
        manager = self.create_manager()
        manager.read_to_filename(self.key_name, self.file_path)
        get_contents_to_filename_mock.assert_called_once_with(self.file_path)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.set_contents_from_file')
    def test_s3_manager_save_file(self, set_contents_from_file_mock):
        manager = self.create_manager()
        manager.save_file(self.key_name, self.file_handle)
        set_contents_from_file_mock.assert_called_once_with(self.file_handle)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.get_contents_to_file')
    def test_s3_manager_read_to_file(self, get_contents_to_file_mock):
        manager = self.create_manager()
        manager.read_to_file(self.key_name)
        get_contents_to_file_mock.assert_called_once_with(mock.ANY)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.set_metadata')
    def test_s3_manager_set_metadata(self, set_metadata_mock):
        manager = self.create_manager()
        manager.set_metadata(self.key_name,
                             self.metadata_key,
                             self.metadata_value)
        set_metadata_mock.assert_called_once_with(self.metadata_key,
                                                  self.metadata_value)
        self.check_manager(manager)

    @mock.patch('integrations.tests.test_s3.S3KeyMock.get_metadata')
    def test_s3_manager_get_metadata(self, get_metadata_mock):
        manager = self.create_manager()
        manager.get_metadata(self.key_name,
                             self.metadata_key)
        get_metadata_mock.assert_called_once_with(self.metadata_key)
        self.check_manager(manager)

    def test_ssl_s3url(self):
        # Subdomain calling format
        self.assertEqual('https://bucket.s3.amazonaws.com/filename',
                         ssl_s3url('bucket', 'filename'))
        # Ordinary calling format
        self.assertEqual('https://s3.amazonaws.com/yet.another.bucket/filename',
                         ssl_s3url('yet.another.bucket', 'filename'))

    def tearDown(self):
        self.key_patcher.stop()
        self.connection_patcher.stop()
        super(S3Test, self).tearDown()
