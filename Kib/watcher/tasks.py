import collections
import json
import os
import tempfile
import uuid

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.files.uploadedfile import SimpleUploadedFile
from dropbox import Dropbox
from dropbox.files import FileMetadata
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from document.tasks import auto_process_file
from portal.models import File
from watcher.models import (
    DropboxAccess, GoogleDriveAccess,
    CloudTypes, CloudFolder, CloudFile,
)

logger = get_task_logger(__name__)


def _create_file_for_dropbox_cloud_file(dropbox_api_client, cloud_file, path):
    download_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    dropbox_api_client.files_download_to_file(path=path,
                                              download_path=download_path)

    file_name = cloud_file.file_name
    batch = cloud_file.folder.batch
    content = SimpleUploadedFile(name=file_name,
                                 content=open(download_path, 'rb').read(),
                                 content_type=None)

    file_object = File.objects.create(file_name=file_name,
                                      batch=batch,
                                      content=content)

    cloud_file.file_object = file_object
    cloud_file.save()

    user = cloud_file.folder.user

    auto_process_file.delay(file_object.pk, user.pk)


@shared_task
def import_files_from_dropbox():
    folders = CloudFolder.objects.select_related(
        'user__dropboxaccess'
    ).prefetch_related(
        'files'
    ).filter(cloud=CloudTypes.DROPBOX)

    folders_by_user = collections.defaultdict(list)
    for folder in folders:
        folders_by_user[folder.user].append(folder)

    imported_files_count = 0

    for user in folders_by_user:
        user_folders = folders_by_user[user]

        try:
            access_token = user.dropboxaccess.token
        except DropboxAccess.DoesNotExist:
            continue

        dropbox_api_client = Dropbox(access_token)

        for folder in user_folders:
            existing_files_ids = {file.file_id for file in folder.files.all()}

            try:
                folder_path_display = dropbox_api_client.files_get_metadata(
                    folder.folder_id
                ).path_display
                current_entries = dropbox_api_client.files_list_folder(
                    folder_path_display
                ).entries
            except Exception as exception:
                logger.error('\nFolder: %s\nException: %s', folder, exception)
                continue

            for entry in current_entries:
                if not isinstance(entry, FileMetadata):
                    continue

                file_id = entry.id

                if file_id in existing_files_ids:
                    continue

                cloud_file = CloudFile.objects.create(folder=folder,
                                                      file_id=file_id,
                                                      file_name=entry.name)

                file_path_display = entry.path_display

                _create_file_for_dropbox_cloud_file(dropbox_api_client,
                                                    cloud_file,
                                                    file_path_display)

                imported_files_count += 1

    logger.info('Files imported from Dropbox: %d', imported_files_count)


def _create_file_for_google_drive_cloud_file(google_drive_api_client, cloud_file):
    download_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    google_drive_file = google_drive_api_client.CreateFile(
        {'id': cloud_file.file_id}
    )
    google_drive_file.GetContentFile(download_path)

    file_name = cloud_file.file_name
    batch = cloud_file.folder.batch
    content = SimpleUploadedFile(name=file_name,
                                 content=open(download_path, 'rb').read(),
                                 content_type=None)

    file_object = File.objects.create(file_name=file_name,
                                      batch=batch,
                                      content=content)

    cloud_file.file_object = file_object
    cloud_file.save()

    user = cloud_file.folder.user

    auto_process_file.delay(file_object.pk, user.pk)


@shared_task
def import_files_from_google_drive():
    folders = CloudFolder.objects.select_related(
        'user__googledriveaccess'
    ).prefetch_related(
        'files'
    ).filter(cloud=CloudTypes.GOOGLE_DRIVE)

    folders_by_user = collections.defaultdict(list)
    for folder in folders:
        folders_by_user[folder.user].append(folder)

    imported_files_count = 0

    for user in folders_by_user:
        user_folders = folders_by_user[user]

        try:
            google_drive_access = user.googledriveaccess
        except GoogleDriveAccess.DoesNotExist:
            continue

        google_auth_client = GoogleAuth()

        # Create a temporary file for reading/writing the client credentials
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as finout:
            json.dump(google_drive_access.credentials, finout)
            finout.flush()

            # Load the saved client credentials from the temporary file
            google_auth_client.LoadCredentialsFile(finout.name)

            if google_auth_client.access_token_expired:
                # Refresh the expired credentials
                google_auth_client.Refresh()
            else:
                # Initialize the credentials
                google_auth_client.Authorize()

            # Save the current credentials to the temporary file
            google_auth_client.SaveCredentialsFile(finout.name)

            finout.seek(0)

            # Update the client credentials in the DB
            google_drive_access.credentials = json.load(finout)
            google_drive_access.save()

        google_drive_api_client = GoogleDrive(google_auth_client)

        for folder in user_folders:
            existing_files_ids = {file.file_id for file in folder.files.all()}

            try:
                current_entries = google_drive_api_client.ListFile(
                    {'q': "'%s' in parents and trashed=false" % folder.folder_id}
                ).GetList()
            except Exception as exception:
                logger.error('\nFolder: %s\nException: %s', folder, exception)
                continue

            for entry in current_entries:
                if entry['mimeType'] == 'application/vnd.google-apps.folder':
                    continue

                file_id = entry['id']

                if file_id in existing_files_ids:
                    continue

                cloud_file = CloudFile.objects.create(folder=folder,
                                                      file_id=file_id,
                                                      file_name=entry['title'])

                _create_file_for_google_drive_cloud_file(google_drive_api_client,
                                                         cloud_file)

                imported_files_count += 1

    logger.info('Files imported from Google Drive: %d', imported_files_count)
