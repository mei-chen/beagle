import os
import logging

from StringIO import StringIO
from boto.s3.connection import (
    S3Connection, OrdinaryCallingFormat, SubdomainCallingFormat
)
from boto.exception import S3ResponseError
from boto.s3.key import Key

from django.conf import settings


class S3FileManager(object):

    @staticmethod
    def _build_s3_keyname(key_prefix, base_folder, file_path):
        """

        Example:
        key_prefix = 'p1/p2'
        base_folder = '/Users/the/folder'
        file_path = '/User/the/folder/sub/file.txt'
        => return p1/p2/folder/sub/file.txt

        :param key_prefix: the prefix folder structure in S3
        :param base_folder: The base folder that wants to be moved
        :param file_path: the absolute path of the file we need transfered
        :return: The proper S3 keyname for a file
        """

        prev_folder = os.path.dirname(base_folder)
        keyname = file_path[len(prev_folder):]
        if keyname[0] == os.path.sep:
            keyname = keyname[1:]

        destination_key = '/'.join((key_prefix, keyname))
        return destination_key

    def __init__(self, access_key_id, secret_access_key, bucket_name, bucket_naming_template='%s', cors_conf=None):
        """
        Given credentials and a bucket name, create the bucket or initialize it

        For the CORS rules, check out he documentation here:
            http://boto.readthedocs.org/en/latest/s3_tut.html#setting-getting-deleting-cors-configuration-on-a-bucket

        :param access_key_id: AWS ACCESS KEY ID
        :param secret_access_key: AWS SECRET ACCESS KEY
        :param bucket_name: the name of the bucket
        :param bucket_naming_template: how to name a bucket
        :param cors_rules: list of cors rules as presented here:
            http://boto.readthedocs.org/en/latest/s3_tut.html#setting-getting-deleting-cors-configuration-on-a-bucket
        """
        self.ACCESS_KEY_ID = access_key_id
        self.SECRET_ACCESS_KEY = secret_access_key

        bucket_name = bucket_naming_template % bucket_name

        self.BUCKET_NAME = bucket_name

        # Unable to use the subdomain calling format,
        # if there is a full stop in the bucket's name
        calling_format_class = (OrdinaryCallingFormat
                                if '.' in self.BUCKET_NAME else
                                SubdomainCallingFormat)
        calling_format = calling_format_class()

        # Open the connection to S3
        self.connection = S3Connection(
            self.ACCESS_KEY_ID,
            self.SECRET_ACCESS_KEY,
            calling_format=calling_format
        )

        try:
            # Try to open the bucket
            self.bucket = self.connection.get_bucket(self.BUCKET_NAME)
        except S3ResponseError:
            # If the bucket is not there then try to create it
            self.bucket = self.connection.create_bucket(self.BUCKET_NAME)
            self.bucket.set_cors = cors_conf

    def build_key(self, key_name):
        """
        Build a S3 key object
        :param key_name: The string key name
        :return:
        """
        s3_key = Key(self.bucket)
        s3_key.key = key_name
        return s3_key

    def delete_key(self, key):
        """
        Delete the specified key from S3
        :param key: the key name string
        """
        s3_key = self.build_key(key)
        s3_key.delete()

    def save_string(self, key, string, acl=None):
        """
        Low level API for saving a string in a file in S3
        If the file is already present, it will overwrite it
        :param key: the key string (it can be a file path)
        :param string: the contents of the file
        """
        s3_key = self.build_key(key)
        s3_key.set_contents_from_string(string)
        if acl is not None:
            s3_key.set_acl(acl)

    def read_to_string(self, key):
        """
        Low level API for reading the contents of a file into a string
        :param key: the key string
        :return:
        """
        s3_key = self.build_key(key)
        try:
            return s3_key.get_contents_as_string()
        except S3ResponseError as e:
            if e.status == 404:
                return None
            raise e

    def save_filename(self, key, file_path, acl=None):
        """
        Low level API for saving a file given the path in S3
        If the file is already present, it will overwrite it
        :param key: the key string (it can be a file path)
        :param file_path: the path of the file
        :return:
        """
        s3_key = self.build_key(key)
        s3_key.set_contents_from_filename(file_path)
        if acl is not None:
            s3_key.set_acl(acl)

    def read_to_filename(self, key, file_path):
        """
        Low level API for getting a file from S3 and saving it locally
        :param key: the key string (it can be a file path)
        :param file_path: the path of the file to write to
        :return:
        """
        s3_key = self.build_key(key)
        s3_key.get_contents_to_filename(file_path)

    def save_file(self, key, file_handle, acl=None):
        """
        API for saving an open file to S3
        :param key: the key string (it can be a file path)
        :param file_handle:
        :param acl:
        :return:
        """
        logging.info('Saving file handle to S3. key=%s', key)

        s3_key = self.build_key(key)
        s3_key.set_contents_from_file(file_handle)
        if acl is not None:
            s3_key.set_acl(acl)

    def read_to_file(self, key):
        """
        API for reading to an open file from S3
        :param key: the key string
        :return: StringIO() instance
        """
        logging.info('Reading file handle from S3. key=%s', key)

        s3_key = self.build_key(key)
        try:
            s = StringIO()
            s3_key.get_contents_to_file(s)
            s.seek(0)
            return s
        except S3ResponseError as e:
            if e.status == 404:
                return None
            raise e

    def save_folder(self, key_prefix, folder_path, acl=None):
        """
        Low level API for saving a folder in S3

        Example:
        key_prefix='p1/p2'
        folder_path = '/Users/the/folder'

        inside S3 this structure will be created:
        p1/p2/{CONTENTS_OF:/Users/the/folder}

        The procedure works recursively for all sub-folders

        :param key_prefix: if a folder structure is desired in S3
        :param folder_path: the path to the folder that needs saved
        :return:
        """
        file_count = 0

        if not os.path.isdir(folder_path):
            return False

        if key_prefix and key_prefix[-1] == '/':
            key_prefix = key_prefix[:-1]

        root_dir = folder_path

        for sub_root, sub_folders, files in os.walk(root_dir):
            for filename in files:
                source_path = os.path.join(sub_root, filename)
                destination_key = self.__class__._build_s3_keyname(key_prefix, folder_path, source_path)
                logging.info("[-] Moving '%s' to '%s' [count=%s]" % (source_path, destination_key, file_count + 1))
                self.save_filename(destination_key, source_path, acl)

                file_count += 1

        return True

    def get_metadata(self, key, metadata_key):
        """
        Get some metadata for a given S3 key
        :param key: the S3 key name
        :param metadata_key: the metadata key on the S3 key
        :return:
        """
        s3_key = self.build_key(key)
        return s3_key.get_metadata(metadata_key)

    def set_metadata(self, key, metadata_key, metadata_value):
        """
        Set some metadata for a given S3 key
        :param key: the S3 key name
        :param metadata_key: the metadata key on the S3 key
        :param metadata_value: the value for the metadata key on the S3 key
        :return:
        """
        s3_key = self.build_key(key)
        s3_key.set_metadata(metadata_key, metadata_value)


def get_s3_bucket_manager(bucket_name, bucket_naming_template="%s"):
    return S3FileManager(settings.AWS_ACCESS_KEY_ID,
                         settings.AWS_SECRET_ACCESS_KEY,
                         bucket_name,
                         bucket_naming_template)


def ssl_s3url(bucket, filename):
    # Unable to use the subdomain calling format,
    #  if there is a full stop in the bucket's name
    if '.' in bucket:
        # Ordinary calling format
        return 'https://s3.amazonaws.com/%s/%s' % (bucket, filename)
    else:
        # Subdomain calling format
        return 'https://%s.s3.amazonaws.com/%s' % (bucket, filename)
