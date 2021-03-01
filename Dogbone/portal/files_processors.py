import json
import os
import zipfile

from beagle_realtime.notifications import NotificationManager
from core.models import Batch
from portal.services import start_document_analysis, save_file_from_request


IGNORED_DIRECTORIES = ('__macosx/',)
ACCEPTED_FILE_EXTENSIONS = ('.pdf', '.docx', '.txt', '.doc',)


def filter_namelist(namelist):
    return [item for item in namelist
            if item.lower().endswith(ACCEPTED_FILE_EXTENSIONS)
            and not item.lower().startswith(IGNORED_DIRECTORIES)]


def notify_batch_empty(batch):
    payload = {'notif': NotificationManager.ServerNotifications.BATCH_EMPTY,
               'batch': batch.to_dict(include_raw=False, include_analysis=False)}
    message = NotificationManager.create_batch_message(batch, 'message', payload)
    message.send()


class FilesUploadProcessor:
    def __init__(self, data, files, user, time_zone=None):
        self.data_info = json.loads(data['info'])
        self.data_name = data.get('batch_name')
        self.files = files
        self.uploader = user
        self.time_zone = time_zone
        # Create base message  for response
        self.message = {
            'errors': False,
            'upload_name': '',
            'upload_id': '',
            'documents': [],
            'e_archives_in_upload': False,
            'encrypted_archives': []
        }

    def get_endpoint_message(self):
        return self.message

    def upload_init(self):
        # Create Batch instance
        batch = Batch.objects.create(
            name=(self.data_name
                  if len(self.data_info) > 1 else
                  self.data_info['0']['file_name']),
            owner=self.uploader,
            pending=True
        )

        # Set Batch instance params for response data
        self.message['upload_name'], self.message['upload_id'] = batch.name, batch.id
        return batch

    def document_handler(self, uploaded_file, batch, file_data, owner):
        # Get file stream and batch
        # Send file to analysis
        document = start_document_analysis(
            uploaded_file=uploaded_file,
            file_name=file_data['file_name'],
            user=owner,
            source=file_data['filesource'],
            batch=batch,
            file_url=file_data['fileurl'],
            token=file_data['accessToken'],
            time_zone=self.time_zone
        )

        if not document:
            self.message['errors'] = True
            return

        self.message['documents'].append({'title': document.title})
        return document

    def zip_archive_handler(self, uploaded_file, batch, file_data, owner):
        # Get zip file stream and batch
        # Save archive in temp dir
        uploaded_archive = save_file_from_request(
            file_name=file_data['file_name'],
            uploaded_file=uploaded_file,
            file_url=file_data['fileurl'],
            token=file_data['accessToken'],
            source=file_data['filesource']
        )

        with zipfile.ZipFile(uploaded_archive, 'r') as archive:
            namelist = filter_namelist(archive.namelist())

            if not namelist:
                # Send a notification if the archive is empty
                # (it doesn't matter whether it is encrypted or not)
                notify_batch_empty(batch)
                # Don't forget to delete the useless empty batch
                # and the corresponding temporary zip archive
                batch.delete()
                os.remove(uploaded_archive)
                return False

            # Check if archive is encrypted
            try:
                archive.testzip()
            except RuntimeError:
                # Set encrypted status to True
                # Add encrypted archive's name and path to response message
                self.message['e_archives_in_upload'] = True
                self.message['encrypted_archives'].append({
                    'name': file_data['file_name'],
                    'path': uploaded_archive
                })
                return False

            # Read files from archive and send to analysis
            for filename in namelist:
                with archive.open(filename, 'r') as stream:
                    document = start_document_analysis(
                        uploaded_file=stream,
                        file_name=filename,
                        user=owner,
                        source='local',
                        batch=batch,
                        time_zone=self.time_zone
                    )
                    self.message['documents'].append({'title': document.title})

        # Make sure to delete the uploaded zip archive, since it is temporary
        os.remove(uploaded_archive)

        return True

    def main(self):
        # Controller method
        # Initial Batch instance
        batch = self.upload_init()

        # Get files from data. If from local then get file stream, else set None
        for file_info in self.data_info:
            try:
                stream = self.files[file_info]
            except:
                stream = None


            file_name = self.data_info[file_info]['file_name']
            # Call zip archive handler if the file is an archive
            if file_name.endswith('.zip'):
                self.zip_archive_handler(
                    uploaded_file=stream,
                    batch=batch,
                    file_data=self.data_info[file_info],
                    owner=self.uploader
                )
            # Call document handler method if the file is not an archive
            else:
                self.document_handler(
                    uploaded_file=stream,
                    batch=batch,
                    file_data=self.data_info[file_info],
                    owner=self.uploader
                )

        return batch


class EncryptedZipArchiveProcessor:
    def __init__(self, data, user, time_zone=None):
        self.data = data
        self.uploader = user
        self.time_zone = time_zone
        self.message = {
            'upload_name': '',
            'upload_id': '',
            'documents': [],
            'e_archives_in_upload': False,
            'encrypted_archives': []
        }

    def get_endpoint_message(self):
        return self.message

    def upload_init(self):
        batch_id = int(self.data['upload_id'])
        batch = Batch.objects.get(id=batch_id)
        self.message['upload_name'], self.message['upload_id'] = batch.name, batch.id
        return batch

    def process_archive(self, batch, path, password, name):
        try:
            with zipfile.ZipFile(path, 'r') as archive:
                namelist = filter_namelist(archive.namelist())

                for filename in namelist:
                    with archive.open(filename, 'r', pwd=password) as stream:
                        document = start_document_analysis(
                            uploaded_file=stream,
                            file_name=filename,
                            user=self.uploader,
                            source='local',
                            batch=batch,
                            time_zone=self.time_zone
                        )
                        self.message['documents'].append({'document': document.title})

            # Make sure to delete the uploaded zip archive, since it is temporary
            os.remove(path)

        except RuntimeError:
            # The current password is wrong, so ask the uploader to enter a new one again
            self.message['e_archives_in_upload'] = True
            self.message['encrypted_archives'].append({
                'name': name,
                'path': path
            })

    def main(self):
        batch = self.upload_init()
        for data in self.data['password']:
            self.process_archive(batch=batch,
                                 path=data['path'],
                                 password=data['password'],
                                 name=data['name'])
        return batch
