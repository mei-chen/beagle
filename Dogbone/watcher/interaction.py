import json
import tempfile

import dropbox
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from watcher.models import Queue, Synchronized


class QueueAdapter(object):

    @staticmethod
    def get_queue_list(folder=None):
        if folder:
            return Queue.objects.filter(folder=folder)
        else:
            return Queue.objects.all()

    def get_ids(self, folder):
        return frozenset(
            self.get_queue_list(folder).values_list('cloud_id', flat=True)
        )


class SynchronizedAdapter(object):

    @staticmethod
    def get_syncronized_list(folder):
        return Synchronized.objects.filter(folder=folder)

    def get_ids(self, folder):
        return frozenset(
            self.get_syncronized_list(folder).values_list('cloud_id', flat=True)
        )


class DropboxInteraction(object):

    @staticmethod
    def auth(folder=None, user=None):
        if folder:
            user = folder.user
        return dropbox.Dropbox(user.dropboxaccess.token)

    @staticmethod
    def get_files_list(access, folder):
        return access.files_list_folder(folder.folder_path).entries

    def check_for_export_folder(self, folder):
        cloud_objects = self.get_files_list(self.auth(user=folder.user), folder)
        for cloud_object in cloud_objects:
            if isinstance(cloud_object, dropbox.files.FolderMetadata):
                return cloud_object._path_display_value
        return False

    def create_dir_on_dropbox(self, access, title, parent_path):
        access.files_create_folder(parent_path + "/" + title)
        return parent_path + "/" + title


class GoogleDriveInteraction(object):

    @staticmethod
    def auth(folder=None, user=None):
        if folder:
            user = folder.user

        drive = GoogleAuth()

        # Create a temporary file for reading/writing the client credentials
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as finout:
            google_drive_access = user.googledriveaccess

            json.dump(google_drive_access.credentials, finout)
            finout.flush()

            # Try to load the saved client credentials from the temporary file
            drive.LoadCredentialsFile(finout.name)
            if drive.access_token_expired:
                # Refresh the expired credentials
                drive.Refresh()
            else:
                # Initialize the saved credentials
                drive.Authorize()
            # Save the current credentials to the temporary file
            drive.SaveCredentialsFile(finout.name)

            finout.seek(0)

            google_drive_access.credentials = json.load(finout)
            google_drive_access.save()

        return GoogleDrive(drive)

    @staticmethod
    def get_files_list(access, folder):
        return access.ListFile(
            {'q': "'%s' in parents and trashed=false" % folder.folder_id}
        ).GetList()

    def create_dir(self, access, title, folder):
        upload = access.CreateFile({'title': title,
                                    "parents": [{"id": folder.folder_id}],
                                    "mimeType": "application/vnd.google-apps.folder"})
        upload.Upload()
        return upload["id"]

    def check_for_export_folder(self, folder):
        objects_meta = self.get_files_list(self.auth(folder=folder), folder)
        for drive_object in objects_meta:
            if drive_object["mimeType"] == "application/vnd.google-apps.folder":
                return drive_object["id"]
        return False
