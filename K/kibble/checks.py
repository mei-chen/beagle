from django.conf import settings
from django.contrib.auth.models import User
from redis import StrictRedis
from watchman.decorators import check

from .celery import app as current_app
from document.models import Document, Sentence
from portal.models import Project, Batch, File


@check
def _check_models():
    users_count = User.objects.all().count()
    projects_count = Project.objects.all().count()
    batches_count = Batch.objects.all().count()
    files_count = File.objects.all().count()
    documents_count = Document.objects.all().count()
    sentences_count = Sentence.objects.all().count()

    return {
        'ok': True,
        'stats': {
            'users': users_count,
            'projects': projects_count,
            'batches': batches_count,
            'files': files_count,
            'documents': documents_count,
            'sentences': sentences_count,
        }
    }


@check
def _check_celery():
    workers = current_app.control.ping()  # list of {hostname: reply} dicts
    if not workers:
        raise RuntimeError('No running celery workers were found.')
    return {
        'ok': True,
        'stats': {
            'workers': len(workers),
        }
    }


@check
def _check_redis():
    connection = StrictRedis.from_url(settings.REDIS_URL)
    connection.ping()  # either returns True or raises ConnectionError
    return {'ok': True}


def models():
    return {'models': _check_models()}


def celery():
    return {'celery': _check_celery()}


def redis():
    return {'redis': _check_redis()}
