import json

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from document.models import Document, PersonalData
from portal.models import File, Batch
from portal.models import Project
from realtime.notify import NotificationManager
from utils.personal_data import find_personal_data, find_personal_data_in_text

logger = get_task_logger(__name__)


@shared_task
def compress_project(project_id, session):
    project = Project.objects.get(pk=project_id)
    archive = None
    notify = {}
    try:
        arc = project.compress()
    except Exception:
        message = "Project compression failed for %s" % project.name
        logger.error(message, exc_info=True)
        notify.update({'message': message, 'level': 'error'})
    else:
        notify.update({'message': 'Archive is ready.', 'level': 'info'})

        archive = {
            'created_at': arc.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            archive['content_file'] = arc.content_file.url
        except ValueError:
            archive['content_file'] = False

    ret = {
        'action': 'compress_project',
        'notify': notify,
        'project_id': project_id,
        'archive': archive
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def gather_personal_data_from_batch(batch_pk, session_key=None):
    batch = Batch.objects.get(pk=batch_pk)
    files = File.objects.filter(batch=batch)
    docs = Document.objects.filter(source_file__in=files)

    docs_to_process = []
    for doc in docs:
        if (doc.content_file and doc.source_file and not
                PersonalData.objects.filter(document=doc).exists()):
            docs_to_process.append(doc)

    ret = {
        'action': 'gather_personal_data_from_batch',
        'batch_id': batch_pk,
        'total_docs': len(docs_to_process),
        'status': 'started'
    }
    message = NotificationManager.notify_client(session_key, ret)
    message.send()

    for i, doc in enumerate(docs_to_process):
        ret['current_doc_idx'] = i
        try:
            pd = find_personal_data(doc)
            for pd_type, text, location in pd:
                PersonalData.objects.create(
                    document=doc,
                    type=pd_type,
                    text=text,
                    location=location
                )
            ret['status'] = 'success'

        except Exception as e:
            logger.warning(e)
            ret['status'] = 'failed'
        message = NotificationManager.notify_client(session_key, ret)
        message.send()

    ret['status'] = 'completed'
    message = NotificationManager.notify_client(session_key, ret)
    message.send()


@shared_task
def gather_personal_data_from_text(text, callback_url, id, uuid):
    result = find_personal_data_in_text(text)
    payload = {
        'personal_data': result,
        'id': id,
        'uuid': str(uuid)
    }

    requests.post(
        callback_url,
        json=json.dumps(payload)
    )
