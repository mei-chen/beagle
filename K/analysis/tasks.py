# App
from realtime.notify import NotificationManager

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger

from document.models import PersonalData, Document
from portal.models import Batch, File
from analysis.models import RegEx, Report, KeywordList
from utils.most_similar.api import MostSimmilarModelAPI
from utils.synonyms.api import SynonymsAPI
from utils.sentence_vector.api import SentenceVectorAPIError

logger = get_task_logger(__name__)


@shared_task
def regex_apply(regex_id, batch_id, session):
    regex = RegEx.objects.get(id=regex_id)
    batch = Batch.objects.get(id=batch_id)

    ret = {
        'notify': {
            'level': 'info',
            'message': "Applying {} to {}".format(regex.name, batch.name)
        },
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()

    # Send positive report
    report = Report(batch=batch)
    report = report.apply_regex(regex)
    if report is None:
        ret = {
            'notify': {
                'level': 'warning',
                'message': "{} nothing found in {}".format(
                    regex.name, batch.name)
            },
        }
    else:
        ret = {
            'action': 'apply_regex',
            'batch': batch_id,
            'notify': {
                'level': 'success',
                'message': "{} is applied to {}".format(regex.name, batch.name)
            },
            'report': {
                'id': report.id,
                'name': report.name,
                'uuid': str(report.uuid),
                'json': report.json
            }
        }
    message = NotificationManager.notify_client(session, ret)
    message.send()

    if not report:
        return

    # Send negative report
    negative_report = Report(batch=batch)
    negative_report = negative_report.apply_regex_negative(regex)
    if negative_report is None:
        ret = {
            'notify': {
                'level': 'warning',
                'message': "{} nothing found in {}".format(
                    regex.name, batch.name)
            },
        }
    else:
        ret = {
            'action': 'apply_regex',
            'batch': batch_id,
            'notify': {
                'level': 'success',
                'message': "{} is applied to {}".format(regex.name, batch.name)
            },
            'negative_report': {
                'id': negative_report.id,
                'name': negative_report.name,
                'uuid': str(negative_report.uuid),
                'json': negative_report.json
            }
        }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def zip_reports(batch, ziptype, report_type, session):
    ret = {
        'action': 'download_reports',
        'success': True,
    }
    try:
        src, ret['url'] = batch.get_zipped_reports(ziptype, report_type)
        ret['notify'] = {
            'level': 'success',
            'message': "Ready to download"
        }
    except Exception:
        logger.warning("Can't zip reports for %s" % batch.name, exc_info=True)
        ret['success'] = False
        ret['notify'] = {
            'level': 'error',
            'message': "Error during generating zip archive"
        }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def most_similar_recommend(word, model, session):
    ret = {
        'notify': {
            'level': 'info',
            'message': "Start suggesting keywords for {}".format(word)
        },
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()

    api = MostSimmilarModelAPI(word, model)
    success, message, result = api.process()
    keywords = result.get('results', [])

    keywords.sort(key=lambda x: x['score'], reverse=True)
    keywords = [keyword['text'] for keyword in keywords]

    ret = {
        'action': 'recommend',
        'notify': {
            'level': 'success' if success else "error",
            'message': message
        },
        'keywords': keywords
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def synonyms_recommend(word, session):
    ret = {
        'notify': {
            'level': 'info',
            'message': "Start suggesting synonyms for {}".format(word)
        },
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()

    api = SynonymsAPI(word)
    success, message, result = api.process()
    keywords = result.get('synonyms', [])

    ret = {
        'action': 'synonyms',
        'notify': {
            'level': 'success' if success else "error",
            'message': message
        },
        'keywords': keywords
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def keywordlist_search(keywordlist_id, batch_id, obfuscate, session):
    keywordlist = KeywordList.objects.get(id=keywordlist_id)
    batch = Batch.objects.get(id=batch_id)

    ret = {
        'notify': {
            'level': 'info',
            'message': "Searching the {} in {}".format(
                keywordlist.name, batch.name
            )
        },
    }
    message = NotificationManager.notify_client(session, ret)
    message.send()
    if obfuscate:
        related_files = File.objects.filter(batch=batch)
        related_docs = Document.objects.filter(source_file__in=related_files)
        stop_words = [
            pd.text.lower()
            for pd in PersonalData.objects.filter(document__in=related_docs)
        ]
    else:
        stop_words = []

    # Send positive report
    report = Report(batch=batch)
    report = report.apply_keyword(keywordlist, stop_words)
    if report is None:
        ret = {
            'notify': {
                'level': 'warning',
                'message': "{} nothing found in {}".format(
                    keywordlist.name, batch.name
                )
            },
        }
    else:
        ret = {
            'action': 'keywordlist_search',
            'batch': batch_id,
            'notify': {
                'level': 'success',
                'message': "{} is applied to {}".format(
                    keywordlist.name, batch.name
                )
            },
            'report': {
                'id': report.id,
                'name': report.name,
                'uuid': str(report.uuid),
                'json': report.json
            }
        }
    message = NotificationManager.notify_client(session, ret)
    message.send()

    if not report:
        return

    # Send negative report
    negative_report = Report(batch=batch)
    negative_report = negative_report.apply_keyword_negative(keywordlist, stop_words)
    if negative_report is None:
        ret = {
            'notify': {
                'level': 'warning',
                'message': "{} nothing found in {}".format(
                    keywordlist.name, batch.name
                )
            },
        }
    else:
        ret = {
            'action': 'keywordlist_search',
            'batch': batch_id,
            'notify': {
                'level': 'success',
                'message': "{} is applied to {}".format(
                    keywordlist.name, batch.name
                )
            },
            'negative_report': {
                'id': negative_report.id,
                'name': negative_report.name,
                'uuid': str(negative_report.uuid),
                'json': negative_report.json
            }
        }
    message = NotificationManager.notify_client(session, ret)
    message.send()


@shared_task
def pull_similar_sentences(sentence, batch_id, session_key):
    batch = Batch.objects.get(id=batch_id)

    payload_start = {
        'notify': {
            'level': 'info',
            'message': 'Pulling similar sentences from {}'.format(batch.name)
        }
    }

    NotificationManager.notify_client(session_key, payload_start).send()

    try:
        report = Report(batch=batch).pull_similar_sentences(sentence)

        alert = getattr(report, 'alert', None)
        if alert is not None:
            payload_alert = {
                'notify': {
                    'level': 'warning',
                    'message': alert
                }
            }
            NotificationManager.notify_client(session_key, payload_alert).send()

    except SentenceVectorAPIError:
        # The API is most probably not working at the moment;
        # even if it is actually broken, we cannot reveal that :)
        payload_finish = {
            'notify': {
                'level': 'error',
                'message': 'Service unavailable. Please try again later...'
            }
        }

    else:
        if report is None:
            payload_finish = {
                'notify': {
                    'level': 'warning',
                    'message': 'Nothing found in {}'.format(batch.name)
                }
            }
        else:
            payload_finish = {
                'notify': {
                    'level': 'success',
                    'message': 'Successfully pulled similar sentences '
                               'from {}'.format(batch.name)
                },
                'action': 'sentences',
                'batch': batch.id,
                'report': {
                    'id': report.id,
                    'name': report.name,
                    'uuid': str(report.uuid),
                    'json': report.json
                }
            }

    NotificationManager.notify_client(session_key, payload_finish).send()
