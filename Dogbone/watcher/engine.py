from __future__ import print_function

import os
import tempfile
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from authentication.models import AuthToken
from core.models import Batch, Document
from dogbone import settings
from integrations.s3 import get_s3_bucket_manager
from richtext.importing import source_handler
from utils import remove_extension
from watcher.interaction import DropboxInteraction, GoogleDriveInteraction
from watcher.models import CloudTypes, Folder, Queue, Synchronized


class HandleCloudFile:

    def get_token(self, queue_obj):
        return AuthToken.objects.get(
            user=Folder.objects.get(id=queue_obj.folder.id).user).token

    def import_dropbox_file(self, folder, queue_obj):
        temp_path = "{}{}{}".format(tempfile.gettempdir(), os.path.sep, os.path.split(queue_obj.cloud_path)[-1])
        DropboxInteraction.auth(folder).files_download_to_file(temp_path, queue_obj.cloud_path)
        return temp_path

    def import_google_drive_file(self, folder, queue_obj):
        temp_path = "{}{}{}".format(tempfile.gettempdir(), os.path.sep, queue_obj.title)
        init_file = GoogleDriveInteraction.auth(folder).CreateFile({'id': queue_obj.cloud_id})
        init_file.GetContentFile(temp_path)
        return temp_path

    def to_analyze(self, queue_obj, cloud):
        from core.tasks import store_activity_notification

        global temp_file
        if cloud == CloudTypes.DROPBOX:
            temp_file = self.import_dropbox_file(queue_obj.folder, queue_obj)
        elif cloud == CloudTypes.GOOGLE_DRIVE:
            temp_file = self.import_google_drive_file(queue_obj.folder, queue_obj)

        with open(temp_file, "rb") as uploaded_file:

            uploader = source_handler("local")

            # Process the upload request
            is_success, payload = uploader.process(uploaded_file=uploaded_file,
                                                   file_url=None,
                                                   file_name=queue_obj.title,
                                                   access_token=None)

        original_filename, temp_file_handle = payload

        # Save locally
        temp_path = default_storage.save(str(uuid.uuid4()), ContentFile(temp_file_handle.read()))
        temp_filename = os.path.join(settings.MEDIA_ROOT, temp_path)

        batch = Batch.objects.create(name=queue_obj.title,
                                     owner=queue_obj.folder.user,
                                     pending=True)

        # TODO: find a way to pass a correct time zone here
        document = Document.analysis_workflow_start(uploader=queue_obj.folder.user,
                                                    file_path=temp_filename,
                                                    upload_source="local",
                                                    original_filename=original_filename,
                                                    title=os.path.splitext(queue_obj.title)[0],
                                                    batch=batch,
                                                    time_zone=None)

        store_activity_notification.delay(
            actor=queue_obj.folder.user,
            recipient=queue_obj.folder.user,
            verb='started processing',
            target=document,
            action_object=document,
            render_string='%s watcher (verb) of (action_object)' % CloudTypes.HUMAN_READABLE[cloud]
        )

        Synchronized.objects.create(
            cloud_id=queue_obj.cloud_id,
            folder=queue_obj.folder,
            original_name=queue_obj.title,
            document=document
        )
        Queue.objects.get(cloud_id=queue_obj.cloud_id).delete()
        os.remove(temp_file)

    def main(self, queue_obj, cloud):
        self.to_analyze(queue_obj, cloud=cloud)


class ExportFileToCloud:

    def get_document_instance(self, document_id):
        return Document.objects.get(id=document_id)

    def get_cloud_instance(self, cloud, document_id):
        if cloud == CloudTypes.DROPBOX:
            return DropboxInteraction.auth(user=self.get_document_instance(document_id).owner)
        elif cloud == CloudTypes.GOOGLE_DRIVE:
            return GoogleDriveInteraction.auth(user=self.get_document_instance(document_id).owner)

    def get_owner_token(self, document):
        return AuthToken.objects.get(user=document.owner).token

    def prepare_document_to_export(self, document, batch=None, include_comments=False,
                                   include_track_changes=False, included_annotations=None):
        from core.tasks import prepare_docx_export

        s3_path = settings.S3_EXPORT_PATH % document.uuid

        prepare_docx_export.delay(
            document.pk,
            s3_path,
            batch=batch,
            include_comments=include_comments,
            include_track_changes=include_track_changes,
            included_annotations=included_annotations,
            user_id=document.owner_id
        )

        return s3_path

    def get_file_to_export(self, document):
        out_filename = '%s.beagle.docx' % remove_extension(document.original_name)
        s3_path = settings.S3_EXPORT_PATH % document.uuid

        # TODO: Get the file handle from S3

        s3_bucket = get_s3_bucket_manager(settings.UPLOADED_DOCUMENTS_BUCKET)
        exported_file = s3_bucket.read_to_file(s3_path)
        with open(out_filename, 'wb') as exp_file:
            exp_file.write(exported_file.read())
        with open(out_filename, 'r') as to_exp:
            return out_filename

    def export_to_dropbox(self, document, folder):
        instance = DropboxInteraction()
        export_file = self.get_file_to_export(document)
        check = instance.check_for_export_folder(folder)
        with open(export_file, "rb") as f:
            file_name = os.path.split(export_file)[-1]
            if check is False:
                instance.create_dir_on_dropbox(DropboxInteraction.auth(user=document.owner), "Analyzed",
                                               folder.folder_path)
                DropboxInteraction.auth(user=document.owner).files_upload(f.read(),"{}{}{}{}{}".format(
                    folder.folder_path,
                    os.path.sep,
                    "Analyzed",
                    os.path.sep,
                    file_name))
            else:
                try:
                    DropboxInteraction.auth(user=document.owner).files_upload(f.read(), "{}{}{}".format(
                        check,
                        os.path.sep,
                        file_name))
                except:
                    return False
        os.remove(export_file)

    def export_to_google_drive(self, document, folder):
        instance = GoogleDriveInteraction()
        export_file = self.get_file_to_export(document)
        check = instance.check_for_export_folder(folder)
        if check is False:
            export_folder = instance.create_dir(GoogleDriveInteraction.auth(user=document.owner), "Analyzed", folder)
            upload = GoogleDriveInteraction.auth(user=document.owner).CreateFile({'title': document.title,
                                                                                  "parents": [{"id": export_folder}]})
            # Create new file instance for google drive on local storage
        else:
            upload = GoogleDriveInteraction.auth(user=document.owner).CreateFile({'title': document.title,
                                                                                  "parents": [{"id": check}]})

            # Set content for instance
        upload.SetContentFile(export_file)
        upload.Upload()
        # Remove temp file
        os.remove(export_file)

    def main(self, document_id, with_export=True):
        document = self.get_document_instance(document_id)
        try:
            folder = Synchronized.objects.get(document=document).folder
        except Synchronized.DoesNotExist:
            return False

        if not with_export:
            self.prepare_document_to_export(document=document)
        else:
            if folder.folder_path:
                self.export_to_dropbox(document=document, folder=folder)
            else:
                self.export_to_google_drive(document=document, folder=folder)
