from __future__ import absolute_import, unicode_literals

import itertools

# Django
from django.contrib.auth.models import User

# App
from realtime.notify import NotificationManager

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger

from portal.models import File
from document.models import Document, Sentence
from utils.sentence_splitting.api import SentenceSplittingRemoteAPI
from utils.sentence_vector.api import SentenceVectorAPI

logger = get_task_logger(__name__)


@shared_task
def convert_file(file_id, session):
    file = File.objects.get(id=file_id)
    NotificationManager.popup_notification(
        session, "Start conversion for {}".format(file.file_name))
    doc = file.convert()
    if doc:
        ret = {
            'action': 'convert_file',
            'file': file.id,
            'document': {
                'name': doc.name,
                'id': doc.id,
                'content_file': doc.content_file.url,
                'text_file': doc.text_file.url
            },
            'notify': {
                'message': 'File {} is converted'.format(file.file_name),
                'level': 'success'
            },
        }
        message = NotificationManager.notify_client(session, ret)
        message.send()
        return doc.id

    else:
        NotificationManager.popup_notification(
            session, "File {} can't be converted!".format(file.file_name),
            'error'
        )


@shared_task
def cleanup_document(tools, document_id, session):
    document = Document.objects.get(id=document_id)

    NotificationManager.popup_notification(
        session, "Start cleanup for {}".format(document.name))

    cleared = document.cleanup(tools, session)

    tags = [tag.name for tag in cleared.tags.all().order_by('order')]
    ret = {
        'action': 'cleanup_document',
        'notify': {
            'level': 'success',
            'message': "{} is cleaned".format(cleared.name)
        },
        'doc': {
            'name': cleared.name,
            'id': cleared.id,
            'tags': tags,
            'cleaned_docx': cleared.cleaned_docx_url,
            'cleaned_txt': cleared.cleaned_txt_url
        }
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def sentence_splitting(document_id, session):
    document = Document.objects.get(id=document_id)
    success = False
    try:
        cleaned_document = document.cleaned
        text_file = cleaned_document.text_file
        # Just check size to ensure that file exists
        text_file.size
    except ValueError:
        message = 'Document {} has no associated text version.'.format(
            document.name
        )
    except Document.DoesNotExist:
        message = 'Document {} has no cleaned copy.'.format(
            document.name
        )
    else:
        NotificationManager.popup_notification(
            session, "Start sentence splitting for %s" % document.name
        )
        api = SentenceSplittingRemoteAPI(text_file)
        success, message, sentences = api.process()

        if success and sentences:
            # Get rid of sentences with low amount of words
            threshold = document.source_file.batch.owner.profile.sentence_word_threshold
            sentences = [s for s in sentences if len(s.split()) >= threshold]

            # Try to perform the most optimal batch vectorization (if possible)
            vectors = SentenceVectorAPI(sentences).vectorize()
            if vectors is None:
                Sentence.objects.bulk_create([
                    Sentence(document=document, text=sentence)
                    for sentence in sentences
                ])
            else:
                Sentence.objects.bulk_create([
                    Sentence(document=document, text=sentence,
                             vectorization=list(vector))
                    for sentence, vector in itertools.izip(sentences, vectors)
                ])

    ret = {
        'action': 'sentence_splitting',
        'notify': {
            'message': message,
            'level': 'success' if success else 'error'
        },
        'success': success,
        'doc': {
            'name': document.name,
            'id': document.id,
        }
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def zip_sentences(batch, session, ziptype):
    NotificationManager.popup_notification(
        session, "Start zip creation for %s" % batch.name
    )
    try:
        src, url = batch.get_zipped_sentences(ziptype)
        success = True
    except Exception:
        logger.warning('Sentence zipping failed', exc_info=True)
        success = False
        url = None

    ret = {
        'action': 'download_sentences',
        'url': url,
        'success': success,
    }
    if not success:
        ret['notify'] = {
            'message': 'Some error is occured on sentence zipping',
            'level': 'error'
        }

    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def auto_process_file(file_pk, user_pk, session_key=None):

    user = User.objects.get(pk=user_pk)
    if not user.profile.file_auto_process:
        return

    instance = File.objects.get(pk=file_pk)
    batch = instance.batch
    ret = {
        'action': 'auto_process_file_started',
        'batch_id': batch.pk,
        'filename': instance.file_name,
        'total_files': batch.files.count()
    }
    message = NotificationManager.notify_client(session_key, ret)
    message.send()

    try:
        doc_pk = convert_file(file_pk, session_key)
        cleanup_document(user.profile.auto_cleanup_tools, doc_pk, session_key)
        sentence_splitting(doc_pk, session_key)
        success = True
        instance.auto_processed = 'success'
        instance.save()

    except Exception as e:
        logger.warning(e)
        success = False
        instance.auto_processed = 'failed'
        instance.save()

    ret['action'] = 'auto_process_file_finished'
    ret['success'] = success
    ret['files_succeeded'] = batch.files.filter(auto_processed='success').count()
    ret['files_failed'] = batch.files.filter(auto_processed='failed').count()
    message = NotificationManager.notify_client(session_key, ret)
    message.send()
