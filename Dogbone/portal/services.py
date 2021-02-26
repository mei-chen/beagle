import os
import tempfile
import uuid
import zipfile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from core.models import Document, SentenceAnnotations
from dogbone import settings
from integrations.s3 import get_s3_bucket_manager
from richtext.importing import source_handler
from utils import remove_extension
from watcher.engine import ExportFileToCloud


def start_document_analysis(uploaded_file, file_name, user, batch,
                            file_url=None, token=None, source=None, time_zone=None):
    uploader = source_handler(source)

    # Process the upload request
    is_success, payload = uploader.process(uploaded_file=uploaded_file,
                                           file_url=file_url,
                                           file_name=file_name,
                                           access_token=token)

    if not is_success:
        return

    original_filename, temp_file_handle = payload
    title = remove_extension(original_filename).replace('_', ' ')

    # Save locally
    temp_path = default_storage.save(str(uuid.uuid4()), ContentFile(temp_file_handle.read()))
    temp_filename = os.path.join(settings.MEDIA_ROOT, temp_path)

    document = Document.analysis_workflow_start(uploader=user,
                                                file_path=temp_filename,
                                                upload_source=source,
                                                original_filename=original_filename,
                                                title=title,
                                                batch=batch,
                                                time_zone=time_zone)
    return document


def save_file_from_request(uploaded_file, file_name, file_url=None, token=None, source=None):
    uploader = source_handler(source)

    # Process the upload request
    is_success, payload = uploader.process(uploaded_file=uploaded_file,
                                           file_url=file_url,
                                           file_name=file_name,
                                           access_token=token)

    original_filename, temp_file_handle = payload

    # Save locally
    temp_path = default_storage.save(str(uuid.uuid4()), ContentFile(temp_file_handle.read()))
    temp_filename = os.path.join(settings.MEDIA_ROOT, temp_path)
    return temp_filename


def get_processed_time(document):
    # Return pretty document processing time
    processing_time = str(document.processing_end_timestamp - document.processing_begin_timestamp).split(':')
    format_processing_time = '{}h {}m {}s'.format(
        processing_time[0],
        processing_time[1],
        processing_time[2].split('.')[0])
    return format_processing_time


def get_annotations(document):
    tags = set()
    sents = document.get_sentences()
    for sent in sents:
        sent_tags = sent.get_tags(excluded=[SentenceAnnotations.KEYWORD_TAG_TYPE])
        tags.update(sent_tags)
    return sorted(tags)


def annotations_to_dict(annotations, global_value=False):
    return {annotation: global_value for annotation in annotations}


def prepare_batch(batch, include_comments=False, include_track_changes=False, include_annotations=None):
    # Make export instance
    export = ExportFileToCloud()

    # Call prepare document task for documents in batch
    for document in batch.get_documents():
        # Get annotations
        if include_annotations:
            annotations = get_annotations(document)
            included_annotations = annotations_to_dict(annotations=annotations, global_value=True)
        else:
            included_annotations = None

        export.prepare_document_to_export(document=document,
                                          batch=batch,
                                          include_comments=include_comments,
                                          include_track_changes=include_track_changes,
                                          included_annotations=included_annotations)

    return True


def get_to_export(document):
    # out_filename = '%s.beagle.docx' % remove_extension(document.original_name)
    s3_path = settings.S3_EXPORT_PATH % document.uuid

    # TODO: Get the file handle from S3

    s3_bucket = get_s3_bucket_manager(settings.UPLOADED_DOCUMENTS_BUCKET)
    exported_file = s3_bucket.read_to_file(s3_path)

    return exported_file.read()


def export_batch(batch):
    # Generate name for exported zip archive
    beagle_zip_extension = '.beagle.zip'
    zip_archive_name = batch.name
    if zip_archive_name.endswith('.zip'):
        zip_archive_name = zip_archive_name[:-4]
    zip_archive_name += beagle_zip_extension

    # Write exported documents to temporary zip archive
    tmp_zip_archive_name = os.path.join(tempfile.gettempdir(), zip_archive_name)
    with zipfile.ZipFile(tmp_zip_archive_name, 'w') as zout:
        docx_extension = '.docx'
        for document in batch.get_documents():
            zout.writestr(remove_extension(document.original_name) + docx_extension,
                          get_to_export(document))

    # Read raw content from temporary zip archive
    with open(tmp_zip_archive_name, 'rb') as zin:
        return zip_archive_name, zin.read()


def get_prepare_batch_status(batch):
    return not batch.get_documents_queryset().filter(prepared=False).exists()


def get_document_parties(document):
    parties = document.get_parties()
    contractor = parties['you']
    company = parties['them']

    return contractor, company
