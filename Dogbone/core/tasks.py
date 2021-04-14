import os
import pytz
import uuid
import logging
import requests
import traceback
import langdetect

from celery import shared_task, chain
from constance import config
from datetime import datetime
from django.conf import settings
from dogbone.tools import absolutify
from django.db.models import Q
from django.utils import timezone
from django.core.files.base import ContentFile
from django.urls import reverse
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from portal.services import get_prepare_batch_status
from utils import conversion
from utils import remove_extension
from ml.facade import LearnerFacade
from ml.capsules import Capsule
from core.exceptions import SpotException
from core.tools import notification_to_dict, init_sample_docs
from core.models import Batch, Document, ExternalInvite, CollaborationInvite, Sentence
from core.models import SentenceAnnotations
from keywords.models import SearchKeyword
from utils.conversion import InvalidDocumentTypeException
from dogbone.exceptions import DocumentSizeOverLimitException
from integrations.tasks import send_slack_message, log_intercom_custom_event
from statistics.tasks import log_statistic_event
from statistics.models import EVENT_TYPES
from integrations.loggers import slack_log
from notifications.models import Notification
from beagle_realtime.notifications import NotificationManager
from utils.EasyPDFCloudAPI.EasyPDFCloudExceptions import EasyPDFCloudHTTPException

from portal.tasks import send_intercom_inapp_message
from portal.mailer import BeagleMailer
from portal.settings import UserSettings


@shared_task
def process_document_task(doc_id, send_notifications=True, send_emails=True, doclevel=True, is_reanalisys=False):
    """
    Handle the document analysis. Send notifications along the way.
    """

    logging.info("Celery: starting `process document task` doc_id=%s" % doc_id)
    try:
        document = Document.objects.get(pk=doc_id)
    except Document.DoesNotExist:
        return False

    if document.is_ready:
        return False

    # Record the time of the processing start and reset the end
    document.processing_begin_timestamp = timezone.now()
    document.processing_end_timestamp = None
    document.save()

    # Send a notification to let UI know that this doc went into Pending state
    payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_PROCESSING_STARTED_NOTIFICATION,
               'document': document.to_dict(include_raw=False, include_analysis=False)}
    message = NotificationManager.create_document_message(document, 'message', payload)
    message.send()

    ####################################################################################################
    #
    # Document Level Analysis (Party identification)
    #
    ####################################################################################################

    if doclevel:
        try:
            payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_PARTY_IDENTIFICATION_STARTED,
                       'document': document.to_dict(include_raw=False, include_analysis=False)}
            message = NotificationManager.create_document_message(document, 'message', payload)
            message.send()

            document.doclevel_analyse()

            # Send parties and agreement type right to frontend
            message = NotificationManager.create_document_message(
                document, 'message', {
                    'notif': {'agreement_type': document.agreement_type,
                              'agreement_parties': document.doclevel_analysis['parties']},
                    'document': document.to_dict(include_raw=False,
                                                 include_analysis=False)})
            message.send()
        except Exception as e:
            document.failed = True
            document.error_message = '[Error while doclevel_analyse]  ' + str(e)
            document.save()

            if settings.DEBUG:
                traceback.print_exc()
            raise e

    ####################################################################################################
    #
    # Old Analysis cleanup (only if this is a reanalysis)
    #
    ####################################################################################################

    if is_reanalisys:
        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_REANALYSIS_STARTED,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

        try:
            sentences = document.get_sentences()
            for s in sentences:
                # Clean only system annotations, not user annotations
                cleaned_annot = []
                if s.annotations and 'annotations' in s.annotations:
                    for a in s.annotations['annotations']:
                        if a['type'] not in (SentenceAnnotations.SUGGESTED_TAG_TYPE,
                                             SentenceAnnotations.ANNOTATION_TAG_TYPE,
                                             SentenceAnnotations.KEYWORD_TAG_TYPE):
                            # Keep it
                            cleaned_annot.append(a)
                    s.annotations['annotations'] = cleaned_annot
                    s.save()
        except Exception as e:
            document.failed = True
            document.error_message = '[Error while cleaning sentences for reanalysis]  ' + str(e)
            document.save()

            if settings.DEBUG:
                traceback.print_exc()
            raise e

    ####################################################################################################
    #
    # DEFAULT TAGS - RLTE Analysis (Responsibilities, Liabilities, Terminations, External References)
    #
    ####################################################################################################

    # Triggers the lazy analysis

    try:
        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_RLTE_ANALYSIS_STARTED,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

        document.analysis_result
        logging.info('Finished RLTE analysis for document %s' % document)
    except Exception as e:
        document.failed = True
        document.error_message = '[Error while document.analysis_result]  ' + str(e)
        document.save()

        if settings.DEBUG:
            traceback.print_exc()
        raise e

    ####################################################################################################
    #
    # ONLINE LEARNERS TAGS + DEFAULT LEARNERS
    #
    ####################################################################################################

    payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_APPLY_LEARNERS_STARTED,
               'document': document.to_dict(include_raw=False, include_analysis=False)}
    message = NotificationManager.create_document_message(document, 'message', payload)
    message.send()

    any_suggested_tag = False
    learners_state = []
    already_added_learners = set()

    try:
        # :capsules list should be treated as immutable
        sentences = document.get_sorted_sentences()
        parties = document.get_parties()
        capsules = [Capsule(s.text, i, parties=parties) for i, s in enumerate(sentences)]
        logging.info('Retrieved %s sentences for document %s' % (len(capsules), document))

        for ol in LearnerFacade.get_all(document.owner, active_only=True, mature_only=True):
            # Add necessary info about learners to the state
            if ol.db_model.tag not in already_added_learners:
                learners_state.append((ol.db_model.tag, ol.db_model.pretrained, ol.db_model.positive_set_size))
                already_added_learners.add(ol.db_model.tag)
            logging.info('Applying the Learner=%s   tag=%s' % (ol, ol.db_model.tag))
            preds = ol.predict(capsules)

            logging.info('Retrieved predictions for document %s for tag=%s' % (document, ol.db_model.tag))
            for i, p in enumerate(preds):
                if p:
                    s = sentences[i]
                    label = ol.db_model.tag
                    s.add_tag(document.owner, label,
                              annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                              classifier_id=ol.db_model.pk)
                    any_suggested_tag = True

    except Exception as e:
        document.failed = True
        document.error_message = '[Error while applying learners]  ' + str(e)
        document.save()

        if settings.DEBUG:
            traceback.print_exc()
        raise e

    document.learners_state = learners_state
    if any_suggested_tag:
        logging.info("The cache has been invalidated")
        document.invalidate_cache()

    ####################################################################################################
    #
    # Apply Spot experiments
    #
    ####################################################################################################

    payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_APPLY_SPOT_EXPERIMENTS_STARTED,
               'document': document.to_dict(include_raw=False, include_analysis=False)}
    message = NotificationManager.create_document_message(document, 'message', payload)
    message.send()

    any_spot_tag = False

    try:
        user_profile = document.owner.details

        spot_experiments = user_profile.spot_experiments
        if not spot_experiments:
            # Exit the outer try-catch block
            raise SpotException('No Spot experiments found.')

        spot_access_token = user_profile.spot_access_token
        if not spot_access_token:
            # Exit the outer try-catch block
            raise SpotException('No Spot API access token found. '
                                'Make sure to authorize your account in Spot.')

        headers = {'X-Access-Token': spot_access_token}

        # Check that the user has access to the Spot API
        ping_url = os.path.join(config.SPOT_API_URL, 'publish', 'ping') + '/'
        ping_response = requests.get(ping_url, headers=headers)
        if not (ping_response.status_code == 200 and ping_response.json()['pong']):
            # Exit the outer try-catch block
            raise SpotException('Could not access Spot API due to failed authentication. '
                                'Make sure to authorize your account in Spot.')

        parties = document.get_parties()
        sentences = document.get_sorted_sentences()
        samples = [Capsule(sentence.text, parties=parties).preprocess() for sentence in sentences]

        not_found_experiments = []

        # Actual names of dogbone tags don't make sense in Spot,
        # so simply use the username of the document's owner
        tag = document.owner.username

        url_template = os.path.join(config.SPOT_API_URL, 'publish', '%s', 'predict') + '/'
        input_json = {'tag': tag, 'samples': samples}

        for experiment_uuid in spot_experiments:
            url = url_template % experiment_uuid

            logging.info('Applying experiment=%s from Spot to document=%s',
                         experiment_uuid, document.uuid)

            response = requests.post(url, json=input_json, headers=headers)

            if response.status_code == 404:
                not_found_experiments.append(experiment_uuid)
                continue

            if response.status_code == 200:
                output_json = response.json()
                predictions = output_json['predictions']
                experiment_metadata = output_json.get('experiment')
                if experiment_metadata is None:
                    experiment_metadata = user_profile.get_spot_experiment(experiment_uuid)
                else:
                    del experiment_metadata['uuid']  # redundant field for metadata
                    # Fetch and save the current number of samples used for training
                    # the corresponding online learner so far
                    online_learner_dict = experiment_metadata.pop('online_learners', {}).get(tag, {})
                    experiment_metadata['samples'] = online_learner_dict.get('samples', 0)
                    # Update metadata after each successful request
                    user_profile.set_spot_experiment(experiment_uuid, experiment_metadata)

                for sentence, prediction in zip(sentences, predictions):
                    if prediction:
                        label = '[Spot] %s' % experiment_metadata['name']
                        sentence.add_tag(document.owner, label,
                                         annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                                         experiment_uuid=experiment_uuid)
                        any_spot_tag = True

        for experiment_uuid in not_found_experiments:
            logging.warning('Removing experiment=%s since it does not exist in Spot anymore.',
                            experiment_uuid)
            user_profile.pop_spot_experiment(experiment_uuid)

    except Exception as e:
        message = 'Error on applying Spot experiments: %r' % e
        if isinstance(e, SpotException):
            logging.warning(message)
        else:
            # An unexpected exception occurred, so also print the stack traceback
            # along with the error message in the DEBUG mode
            if settings.DEBUG:
                logging.exception(message)
            else:
                logging.error(message)

    if any_spot_tag:
        logging.info("The cache has been invalidated")
        document.invalidate_cache()

    ####################################################################################################
    #
    # Search for keywords
    #
    ####################################################################################################

    payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_KEYWORDS_SEARCH_STARTED,
               'document': document.to_dict(include_raw=False, include_analysis=False)}
    message = NotificationManager.create_document_message(document, 'message', payload)
    message.send()

    any_keyword_tag = False
    keywords_state = []
    try:
        active_keywords = SearchKeyword.activated.filter(owner=document.owner)
        sentences = document.get_sentences()
        keywords_state = [(kw.keyword, kw.exact_match) for kw in active_keywords]

        for sentence in sentences:
            for kw in active_keywords:
                if kw.matches(sentence.text):
                    sentence.add_tag(document.owner, kw.keyword,
                                     annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)
                    any_keyword_tag = True
    except Exception as e:
        document.failed = True
        document.error_message = '[Error while applying keywords]  ' + str(e)
        document.save()

        if settings.DEBUG:
            traceback.print_exc()
        raise e

    document.keywords_state = keywords_state
    if any_keyword_tag:
        logging.info("The cache has been invalidated")
        document.invalidate_cache()

    document.pending = False
    document.save()

    logging.info("Pending flag set to false for document=%s and saving" % document)

    if send_notifications:
        # Sending the document complete notifications
        logging.info('Sending API request for dispatching notifications')

        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_COMPLETED_NOTIFICATION,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

    # -- Log a document process event in Intercom --

    # Get RLTE Counts
    resp, liab, term, extref = 0, 0, 0, 0

    # Skip agreements with no cached analysis
    if document.analysis_result is None:
        resp, liab, term, extref = -1, -1, -1, -1
    else:
        try:
            for s in document.analysis_result['sentences']:
                annotations = s['annotations']
                # Count RLTs
                if annotations is not None:
                    for a in annotations:
                        label = a['label']
                        if label == 'RESPONSIBILITY':
                            resp += 1
                        elif label == 'LIABILITY':
                            liab += 1
                        elif label == 'TERMINATION':
                            term += 1
                # Count Es
                if s['external_refs'] is not None:
                    extref += len(s['external_refs'])
        except TypeError as e:
            logging.error('Error extracting metadata from document=%s. Exception: %s' % (str(document.uuid), str(e)))
            send_slack_message('Error extracting metadata from document=%s. Exception: %s' % (str(document.uuid), str(e)), '#dev')

    # Compute mean party confidence
    confidence_them = document.doclevel_analysis['parties']['them']['confidence']
    confidence_you = document.doclevel_analysis['parties']['you']['confidence']
    confidence_mean = ((confidence_them + confidence_you) / 2)

    # Actually send the intercom event
    processed_metadata = {
        'Title': document.title,
        'Party Confidence Mean': confidence_mean,
        'Report Url': {'url': absolutify(document.get_report_url()), 'value': 'View Report'},
        'Responsibilities': resp,
        'Liabilities': liab,
        'Terminations': term,
        'External References': extref
    }
    log_intercom_custom_event.delay(email=document.owner.email,
                                    event_name=EVENT_TYPES['document_processed'],
                                    metadata=processed_metadata)
    # Also send the same event to statistics
    log_statistic_event.delay(event_name='document_processed',
                              event_user_id=document.owner.id,
                              event_data=processed_metadata)

    # If the confidence is low, notify the front end of the WEAK_DOCUMENT_ANALYSIS
    if confidence_mean < 40 or confidence_you < 25 or confidence_them < 25:
        # If this is production let us know on slack.
        if not settings.DEBUG:
            if confidence_mean < 40:
                low_conf = confidence_mean
                msg = (u'{0} {1} ({2}) recieved a low party confidence mean of '
                       u'{3}%\nR: *{4}*\nL: *{5}*\nT: *{6}*\nE: *{7}*\non document _{8}_')
            else:
                low_conf = confidence_you if (confidence_you < confidence_them) else confidence_them
                msg = (u'{0} {1} ({2}) recieved a low party confidence of '
                       u'{3}%\nR: *{4}*\nL: *{5}*\nT: *{6}*\nE: *{7}*\non document _{8}_')

            send_slack_message(msg.format(document.owner.first_name,
                                          document.owner.last_name,
                                          document.owner.email,
                                          low_conf,
                                          resp,
                                          liab,
                                          term,
                                          extref,
                                          document.title), '#intercom')

        payload = {'notif': NotificationManager.ServerNotifications.WEAK_DOCUMENT_ANALYSIS,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

    # Record the time of the processing end
    document.processing_end_timestamp = timezone.now()
    document.save()

    batch = document.batch

    if batch and batch.is_analyzed:
        if send_notifications:
            payload = {'notif': NotificationManager.ServerNotifications.BATCH_PROCESSING_COMPLETED,
                       'batch': batch.to_dict(include_raw=False, include_analysis=False, include_docstats=True)}
            message = NotificationManager.create_batch_message(batch, 'message', payload)
            message.send()

        if send_emails:
            # In the case of reanalysis always send individual digest emails
            # for each processed document despite the existing batch
            if batch.is_trivial or is_reanalisys:
                send_document_digest.delay(document.pk, is_reanalisys)
            else:
                # Make sure to clean up the batch only after
                # sending an appropriate email to the user
                chain(send_batch_processed_notification.si(batch.pk),
                      cleanup_batch.si(batch.pk)).delay()

        elif not batch.is_trivial:
            cleanup_batch.delay(batch.pk)

    elif not batch and send_emails:
        send_document_digest.delay(document.pk, is_reanalisys)

    logging.info("Celery: finished `process document task` doc_id=%s" % doc_id)
    logging.info('Official processing time: %ds' % (
        document.processing_end_timestamp - document.processing_begin_timestamp
    ).total_seconds())

    return True


def handle_invalid_document(document, send_notifications=False, notif=None, error=None, send_emails=False):
    batch = document.batch
    batch.add_invalid_document(document)

    if send_notifications:
        payload = {'document': document.to_dict(include_raw=False, include_analysis=False)}
        if notif:
            payload['notif'] = notif
        if error:
            payload['error'] = error
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

    # All the documents in the batch turned out to be invalid,
    # or the batch were already processed (the case when an invalid document
    # is handled at the end of the batch processing)
    if batch.documents_count == batch.invalid_documents_count or batch.is_analyzed:
        # If there is at least one valid document and the batch is processed,
        # then don't forget to send an appropriate notification
        if batch.documents_count != batch.invalid_documents_count and batch.is_analyzed and send_notifications:
            payload = {'notif': NotificationManager.ServerNotifications.BATCH_PROCESSING_COMPLETED,
                       'batch': batch.to_dict(include_raw=False, include_analysis=False, include_docstats=True)}
            message = NotificationManager.create_batch_message(batch, 'message', payload)
            message.send()

        if send_emails:
            if batch.is_trivial:
                send_email_task = send_document_processing_error_notification
                object_pk = document.pk
            else:
                send_email_task = send_batch_processed_notification
                object_pk = batch.pk

            # Make sure to clean up the batch only after
            # sending an appropriate email to the user
            chain(send_email_task.si(object_pk),
                  cleanup_batch.si(batch.pk)).delay()

        else:
            cleanup_batch.delay(batch.pk)


@shared_task
def cleanup_batch(batch_id):
    try:
        batch = Batch.objects.get(pk=batch_id)
    except Batch.DoesNotExist:
        return False

    for invalid_document in batch.get_invalid_documents():
        batch.remove_document(invalid_document)
        batch.remove_invalid_document(invalid_document)
        # Clean up the invalid document model
        invalid_document.delete()

    if batch.is_empty:
        # The batch becomes empty, i.e. all the documents
        # inside it were invalid and hence were deleted,
        # so this batch also can be deleted
        batch.delete()

    return True


#@shared_task
def process_document_conversion(doc_id, temp_filename, send_notifications=True, send_emails=True):
    """
    Handle the document conversion. Send notifications along the way.
    If :report_url is None, socket messages won't be sent.

    :param doc_id: The primary key of the document model
    :param temp_filename: file handle
    :param send_notifications: If notifications should be dispatched to the user or not
    :param send_emails: If email notifications should be dispatched ot not
    :return: True/False
    """

    logger = logging.getLogger(__name__)
    # logger.addHandler(slack_handler)

    logger.info("Celery: started `process document conversion` doc_id=%s" % doc_id)

    ####################################################################################################
    #
    # Check that the document model exists in the database
    #
    ####################################################################################################
    try:
        document = Document.objects.get(pk=doc_id)
    except Document.DoesNotExist:
        message = 'process_document_conversion: Document model pk=%s not found at conversion stage' % doc_id
        logger.error(message)
        slack_log(message, logging.ERROR)
        return False

    ####################################################################################################
    #
    # Confirm that the uploaded stage ended
    #
    ####################################################################################################

    if send_notifications:
        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_UPLOADED_NOTIFICATION,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        NotificationManager.create_document_message(document, 'message', payload).send()

    ####################################################################################################
    #
    # Start the convert stage
    #
    ####################################################################################################

    filename, extension = os.path.splitext(document.original_name)

    try:
        formatted_sents_tuple = conversion.document2sentences(document,
                                                              temp_filename,
                                                              extension)

    except EasyPDFCloudHTTPException as e:
        message = 'process_document_conversion: Got an EasyPDF error on converting %s. Exception %s uploader=%s' \
                  % (str(document.uuid), str(e), str(document.owner))
        logger.error(message)
        slack_log(message, logging.ERROR)

        send_intercom_inapp_message.delay(from_id=settings.INTERCOM_STAFF['BeagleSupport'],
                                          to_email=document.owner.email,
                                          message=settings.EASYPDF_ERROR_MESSAGE)

        # Log event to Intercom
        metadata = {
            'Title': document.title,
            'Error': 'EasyPDF error. Exception: %s' % str(e)
        }
        log_intercom_custom_event.delay(email=document.owner.email,
                                        event_name=EVENT_TYPES['document_conversion_error'],
                                        metadata=metadata)
        # Log event to Statistics
        log_statistic_event.delay(event_name='document_conversion_error',
                                  event_user_id=document.owner.id,
                                  event_data=metadata)

        handle_invalid_document(
            document,
            send_notifications=send_notifications,
            notif=NotificationManager.ServerNotifications.EASYPDF_ERROR,
            error=str(e),
            send_emails=send_emails
        )

        return False

    except InvalidDocumentTypeException as e:
        message = 'process_document_conversion: Document %s (%s) format not supported, uploader=%s' % (
            document.original_name, str(document.uuid), str(document.owner))
        logger.error(message)
        slack_log(message, logging.ERROR)

        # Log event to Intercom
        metadata = {
            'Title': document.title,
            'Error': 'Document format not supported (%s)' % document.original_name.split('.')[-1]
        }
        log_intercom_custom_event.delay(email=document.owner.email,
                                        event_name=EVENT_TYPES['document_conversion_error'],
                                        metadata=metadata)
        # Log event to Statistics
        log_statistic_event.delay(event_name='document_conversion_error',
                                  event_user_id=document.owner.id,
                                  event_data=metadata)

        handle_invalid_document(
            document,
            send_notifications=send_notifications,
            notif=NotificationManager.ServerNotifications.DOCUMENT_ERROR_FORMAT_UNSUPPORTED_NOTIFICATION,
            send_emails=send_emails
        )

        return False

    except DocumentSizeOverLimitException as e:
        message = 'process_document_conversion: Document %s (%s) has too many pages to be OCRed, uploader=%s' % (
            document.original_name, str(document.uuid), str(document.owner))
        logger.error(message)
        slack_log(message, logging.ERROR)

        # Log event to Intercom
        metadata = {
            'Title': document.title,
            'Error': 'Document has too many pages to be OCRed (%s)' % document.original_name.split('.')[-1]
        }
        log_intercom_custom_event.delay(email=document.owner.email,
                                        event_name=EVENT_TYPES['document_too_large_to_ocr'],
                                        metadata=metadata)
        # Log event to Statistics
        log_statistic_event.delay(event_name='document_too_large_to_ocr',
                                  event_user_id=document.owner.id,
                                  event_data=metadata)

        handle_invalid_document(
            document,
            send_notifications=send_notifications,
            notif=NotificationManager.ServerNotifications.DOCUMENT_ERROR_TOO_LARGE_TO_OCR,
            send_emails=send_emails
        )

        return False

    except Exception as e:
        # The document could not be converted, most probably malformed
        message = 'process_document_conversion: Error on converting %s. Got exception: %s uploader=%s' \
                  % (str(document.uuid), str(e), str(document.owner))
        # An unexpected exception occurred, so also print the stack traceback
        # along with the error message in the DEBUG mode
        if settings.DEBUG:
            logger.exception(message)
        else:
            logger.error(message)
        slack_log(message, logging.ERROR)

        # Log event to Intercom
        metadata = {
            'Title': document.title,
            'Error': 'Exception: %s' % str(e)
        }
        log_intercom_custom_event.delay(email=document.owner.email,
                                        event_name=EVENT_TYPES['document_conversion_error'],
                                        metadata=metadata)
        # Log event to Statistics
        log_statistic_event.delay(event_name='document_conversion_error',
                                  event_user_id=document.owner.id,
                                  event_data=metadata)

        handle_invalid_document(
            document,
            send_notifications=send_notifications,
            notif=NotificationManager.ServerNotifications.DOCUMENT_ERROR_MALFORMED_NOTIFICATION,
            error=str(e),
            send_emails=send_emails
        )

        return False

    finally:
        # Remove the temp file
        if os.path.isfile(temp_filename):
            os.remove(temp_filename)

        # Remove the temp file
        if os.path.isfile(temp_filename + '.txt'):
            os.remove(temp_filename + '.txt')

        # Remove the temp file
        if os.path.isfile(temp_filename + '.docx'):
            os.remove(temp_filename + '.docx')

        # Remove the temp file
        if os.path.isfile(temp_filename + '.pdf'):
            os.remove(temp_filename + '.pdf')

        # Remove the temp file
        if os.path.isfile(temp_filename + '.doc'):
            os.remove(temp_filename + '.doc')

    ####################################################################################################
    #
    # Check if the conversion stage was successful
    #
    ####################################################################################################

    if formatted_sents_tuple is None:
        message = 'process_document_conversion: Document %s (%s) format not supported uploader=%s' % (
            document.original_name, str(document.uuid), str(document.owner))
        logger.error(message)
        slack_log(message, logging.ERROR)

        # Log event to Intercom
        metadata = {
            'Title': document.title,
            'Error': 'Document format not supported (%s)' % document.original_name.split('.')[-1]
        }
        log_intercom_custom_event.delay(email=document.owner.email,
                                        event_name=EVENT_TYPES['document_conversion_error'],
                                        metadata=metadata)
        # Log event to Statistics
        log_statistic_event.delay(event_name='document_conversion_error',
                                  event_user_id=document.owner.id,
                                  event_data=metadata)

        handle_invalid_document(
            document,
            send_notifications=send_notifications,
            notif=NotificationManager.ServerNotifications.DOCUMENT_ERROR_FORMAT_UNSUPPORTED_NOTIFICATION,
            send_emails=send_emails
        )

        return False

    ####################################################################################################
    #
    # Check the language of the document. Allow En only
    #
    ####################################################################################################

    rawtext = ' '.join(formatted_sents_tuple[0]).strip()
    if rawtext:
        lang = langdetect.detect(rawtext)
        logger.debug('Detected language: %s' % lang)

        if lang != 'en':
            message = 'Document language not supported: %s (%s) Document=%s uploader=%s' \
                      % (lang, document.original_name.split('.')[-1], document.uuid, str(document.owner))
            logger.error(message)
            slack_log(message, logging.ERROR)

            # Log event to Intercom
            metadata = {
                'Title': document.title,
                'Error': 'Document language not supported: %s (%s)' % (lang, document.original_name.split('.')[-1])
            }
            log_intercom_custom_event.delay(email=document.owner.email,
                                            event_name=EVENT_TYPES['document_language_error'],
                                            metadata=metadata)
            # Log event to Statistics
            log_statistic_event.delay(event_name='document_language_error',
                                      event_user_id=document.owner.id,
                                      event_data=metadata)

            handle_invalid_document(
                document,
                send_notifications=send_notifications,
                notif=NotificationManager.ServerNotifications.DOCUMENT_ERROR_UNSUPPORTED_LANGUAGE_NOTIFICATION,
                send_emails=send_emails
            )

            return False

    ####################################################################################################
    #
    # Save the extracted sentences to the document model
    #
    ####################################################################################################

    document.init(*formatted_sents_tuple)
    document.save()

    ####################################################################################################
    #
    # Start the analysis phase
    #
    ####################################################################################################

    process_document_task.delay(doc_id=document.pk, send_notifications=send_notifications, send_emails=send_emails)
    logger.info("Celery: finished `process document conversion` doc_id=%s" % doc_id)

    ####################################################################################################
    #
    # Confirm that the conversion stage ended successfully
    #
    ####################################################################################################
    if send_notifications and document.batch.is_trivial:
        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_CONVERTED_NOTIFICATION,
                   'document': document.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(document, 'message', payload)
        message.send()

    return True


@shared_task
def prepare_docx_export(doc_id, s3_path, batch=None, include_comments=False, include_track_changes=False,
                        included_annotations=None, user_id=None):
    """
    Runs the document export task.

    Args:
        doc_id: The document id to export.
        s3_path: ???.
        include_comments (:obj:`bool`, optional): If to export with comments
        include_track_changes (:obj:`bool`, optional): If to export with tracked changes
        included_annotations (:obj:`dict`, optional): Annotations with flags True/False
        user_id (:obj:`int`, optional): In case of error notify the uploader of the error

    Returns:
        This is a description of what is returned.

    Raises:
        KeyError: Raises an exception.
    """

    from richtext.exporting import document_to_docx, document_to_rich_docx

    logger = logging.getLogger(__name__)
    logger.info("Celery: `prepare_docx_export` with doc_id=%s" % doc_id)
    doc = Document.objects.get(pk=doc_id)

    try:
        if doc.docx_s3:
            document_to_rich_docx(
                doc,
                s3_path,
                include_comments=include_comments,
                include_track_changes=include_track_changes,
                included_annotations=included_annotations
            )
        else:
            document_to_docx(
                doc,
                s3_path,
                include_comments=include_comments,
                include_track_changes=include_track_changes,
                included_annotations=included_annotations
            )

        # Notify that it's finished through a socket notif
        payload = {'notif': NotificationManager.ServerNotifications.DOCUMENT_EXPORT_READY,
                   'document': doc.to_dict(include_raw=False, include_analysis=False)}
        message = NotificationManager.create_document_message(doc, 'message', payload)
        message.send()

        if batch:
            # If document is from batch, turn on prepared status
            doc.prepared = True
            doc.save()

            # Check if all documents in batch are prepared to export
            if get_prepare_batch_status(batch):
                payload = {'notif': NotificationManager.ServerNotifications.BATCH_EXPORT_READY,
                           'batch': batch.to_dict(include_raw=False, include_analysis=False)}
                message = NotificationManager.create_batch_message(batch, 'message', payload)
                message.send()

                batch.get_documents_queryset().update(prepared=False)

    except Exception as e:
        message = 'Exception in document (id: %s) export task: %s' % (doc_id, e)
        logger.error(e, exc_info=True)
        slack_log(message, logging.ERROR)

        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return
            payload = {
                'notif': NotificationManager.ServerNotifications.DOCUMENT_EXPORT_ERROR,
                'error': '%s' % e,
                'document': doc.to_dict(include_raw=False, include_analysis=False)
            }
            message = NotificationManager.create_user_message(user, 'message', payload)
            message.send()


@shared_task
def initialize_sample_docs(user_id):

    # get user from id
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return 
    
    samples = init_sample_docs()

    for s in samples:
        spath = os.path.join(settings.SAMPLE_DOCS_DIR, s)

        doc = Document(owner=user,
                       original_name=s,
                       title=remove_extension(s).replace('_', ' '),
                       initsample=True,
                       pending=True)
        doc.save()

        # Save locally
        with open(spath) as file_handle:
            tmppath = default_storage.save(str(uuid.uuid4()),
                                           ContentFile(file_handle.read()))
            temp_filename = os.path.join(settings.MEDIA_ROOT, tmppath)

        # Send the file to the other tasks in the Celery process pipeline
        process_document_conversion.delay(doc.pk, temp_filename,
                                          send_notifications=True,
                                          send_emails=False)


@shared_task
def install_pretrained(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logging.error("User %s does not exist" % (user_id))
        return

    """ Generates a Learner for all the pretrained learners available """
    for pl in LearnerFacade.get_all(preload=False):
        if pl.db_model.exclusivity and pl.db_model.exclusivity != user.username:
            continue

        logging.info('Adding pretrained learner pl=%s for user=%s' % (pl, user))
        LearnerFacade.get_or_create(pl.db_model.tag, user, preload=False)
    logging.info("All pre-trained models have been added to the user")


##################################################################################################
#
#  Email Tasks
#
##################################################################################################


@shared_task
def send_external_invite(external_invite_id, signup_url):
    try:
        external_invite = ExternalInvite.objects.get(pk=external_invite_id)
    except ExternalInvite.DoesNotExist:
        return False

    logging.info("Sending email for external_invite: %s", external_invite)
    success = BeagleMailer.send_external_invite(external_invite, signup_url)

    if success:
        external_invite.email_sent_date = timezone.now()
        external_invite.save()
    else:
        logging.error("Could not send email for external invite: %s", external_invite)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_collaboration_invite(collaboration_invite_id, follow_url):
    try:
        collaboration_invite = CollaborationInvite.objects.get(pk=collaboration_invite_id)
    except CollaborationInvite.DoesNotExist:
        return False

    # Check if allowed by user settings
    settings = UserSettings(collaboration_invite.invitee)
    if settings.get_setting('collaboration_invite_notification'):
        logging.info("Sending email for collaboration_invite: %s", collaboration_invite)
        success = BeagleMailer.send_collaboration_invite(collaboration_invite, follow_url)
    else:
        logging.info("Sending collaboration_invite email notif FORBIDDEN by user settings: %s", collaboration_invite)
        success = True

    if not success:
        logging.error("Could not send email for collaboration invite: %s", collaboration_invite)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_owner_changed(old_owner_id, document_id):
    try:
        document = Document.objects.get(pk=document_id)
        old_owner = User.objects.get(pk=old_owner_id)
    except (User.DoesNotExist, Document.DoesNotExist):
        return False

    # Check if allowed by user settings
    settings = UserSettings(document.owner)
    if settings.get_setting('owner_changed_notification'):
        logging.info("Sending email for owner changed: document=%s", document)
        success = BeagleMailer.send_owner_changed(old_owner, document)
    else:
        logging.info("Sending owner_changed email notif FORBIDDEN by user settings: document=%s", document)
        success = True

    if not success:
        logging.error("Could not send email for owner changed: document=%s", document)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_user_was_mentioned(mention_author_id, mentioned_user_id,
                            sentence_id, sentence_index):
    try:
        mention_author = User.objects.get(pk=mention_author_id)
        mentioned_user = User.objects.get(pk=mentioned_user_id)
        sentence = Sentence.objects.get(pk=sentence_id)
    except (User.DoesNotExist, Sentence.DoesNotExist):
        return False

    logging.info("Sending email to %s mentioned by %s in %s (idx=%d)",
                 mentioned_user, mention_author, sentence.doc, sentence_index)

    success = BeagleMailer.send_user_was_mentioned(
        mention_author, mentioned_user, sentence, sentence_index
    )

    if not success:
        logging.error("Could not send email for user mention: document=%s", sentence.doc)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_password_request(password_request_id, reset_url):
    from authentication.models import PasswordResetRequest
    try:
        password_request = PasswordResetRequest.objects.get(pk=password_request_id)
    except PasswordResetRequest.DoesNotExist:
        return False

    logging.info("Sending email for password reset: %s", password_request)
    success = BeagleMailer.send_password_request(password_request, reset_url)

    if success:
        password_request.email_sent_date = timezone.now()
    else:
        logging.error("Could not send email for password request: %s", password_request)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_document_complete_notification(document_id):
    """ Would seem that `send_document_digest` is now prefered over this one """
    from authentication.models import OneTimeLoginHash
    try:
        document = Document.objects.get(pk=document_id)
        user = document.owner
    except Document.DoesNotExist:
        return False

    logging.info("Sending email document complete for: %s", document)

    # If the user has never logged in yet, send the document complete notification with a login hash
    if user.details.initial_tour is None:
        login_hash = OneTimeLoginHash.create(user)
        document_url = absolutify("%s?next=%s&hash=%s" % (
            reverse('login'), document.get_report_url(), login_hash.get_hash())
        )
    else:
        document_url = absolutify(document.get_report_url())

    success = BeagleMailer.document_complete_notification(user, document, document_url)

    if not success:
        logging.error("Could not send complete notification email for document=%s", document)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_document_digest(document_id, is_reanalysis=False):
    """ Sent on document processing finish """
    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        return False

    # Check if allowed by owner settings
    owner = document.owner
    settings = UserSettings(owner)
    if settings.get_setting('finished_processing_notification'):
        logging.info("Sending email document digest: %s to user: %s", document, owner)
        success = BeagleMailer.send_document_digest(owner, document, is_reanalysis)
        if is_reanalysis:
            # Also notify all collaborators, but ignore results
            for collaborator in document.collaborators:
                BeagleMailer.send_document_digest(collaborator, document, is_reanalysis)
    else:
        logging.info("Sending document digest email FORBIDDEN by user settings: %s to user: %s", document, owner)
        success = True

    if not success:
        logging.error("Could not send digest email for document=%s", document)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_batch_processed_notification(batch_id):
    """ Sent on batch processing finish """
    try:
        batch = Batch.objects.get(pk=batch_id)
    except Batch.DoesNotExist:
        return False

    # Check if allowed by owner settings
    owner = batch.owner
    settings = UserSettings(owner)
    if settings.get_setting('finished_processing_notification'):
        logging.info("Sending email batch processed notification: %s to user: %s", batch, owner)
        success = BeagleMailer.send_batch_processed_notification(owner, batch)
    else:
        logging.info("Sending batch processed notification email FORBIDDEN by user settings: %s to user: %s", batch, owner)
        success = True

    if not success:
        logging.error("Could not send processed notification email for batch=%s", batch)
        raise BeagleMailer.UnsentEmailException()

    return True


@shared_task
def send_auto_account_created_notification(onetime_login_hash_id):
    from authentication.models import OneTimeLoginHash
    h = OneTimeLoginHash.objects.get(pk=onetime_login_hash_id)
    if not h.resolved:
        BeagleMailer.auto_account_creation_notification(h)


@shared_task
def send_document_uploaded_via_email_notification(document_id):
    if hasattr(settings, 'CLIENT_NAME') and getattr(settings, 'CLIENT_NAME') == 'WESTPAC':
        return

    try:
        document = Document.objects.get(pk=document_id)
        BeagleMailer.document_uploaded_via_email_notification(document)
    except Document.DoesNotExist:
        pass


@shared_task
def send_document_processing_error_notification(document_id):
    logging.info("In task send_document_processing_error_notification with document_id=%s" % document_id)
    try:
        document = Document.objects.get(pk=document_id)
        return BeagleMailer.document_processing_error_notification(document)
    except Document.DoesNotExist:
        logging.error("Could not find document with pk=%s" % document_id)
        return False


@shared_task
def send_unsupported_file_type_notification(user_id, title):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(pk=user_id)
        BeagleMailer.unsupported_file_type_error_notification(user, title)
    except User.DoesNotExist:
        pass


@shared_task
def send_help_notification(user_id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(pk=user_id)
        BeagleMailer.help_notification(user)
    except User.DoesNotExist:
        pass


@shared_task
def send_attachments_not_found_notification(user_id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(pk=user_id)
        BeagleMailer.attachments_not_found_notification(user)
    except User.DoesNotExist:
        pass


##################################################################################################
#
#  Activity Tasks
#
##################################################################################################

@shared_task
def bounce_delayed_notifications(email):
    from core.models import DelayedNotification

    delayed_notifications = DelayedNotification.objects.filter(email__iexact=email)
    for delayed_notification in delayed_notifications:
        delayed_notification.create_notification()


@shared_task
def parse_comments_on_external_invite_delete(document_ids, user_id):
    from core.models import Sentence
    from core.signals import comment_posted
    from django.contrib.auth.models import User
    documents = Document.objects.filter(id__in=document_ids)
    for document in documents:
        try:
            user = User.objects.get(id=user_id)
            sentences = Sentence.objects.filter(doc=document,
                                                comments__icontains='@[%s](%s)' % (user.email, user.email))
            for sentence in sentences:
                for comment in sentence.comments['comments']:
                    comment['message'] = comment['message'].replace(
                        '@[%s](%s)' % (user.email, user.email),
                        '@[%s](%s)' % (user.username, user.email))

                    comment_posted.send(sender=Sentence,
                                        sentence=sentence,
                                        author=User.objects.get(username=comment['author']),
                                        comment=comment['message'],
                                        created=comment['timestamp'])

                    logging.info('"comment_posted" signal emitted in '
                                 'parse_comments_on_external_invite_delete '
                                 'for "%s", comment author: "%s"' % (str(document), user.username))
                sentence.save()

        except Exception as e:
            logging.error('Exception occurred in "parse_comments_on_external_invite_delete": %s', str(e))


@shared_task
# modify this to use id
def store_activity_notification(actor_id, recipient_id, verb, target_id=None, target_type=None,
                                action_object_id=None, action_object_type=None, render_string=None, transient=False, created=None):
    """
    Task used for storing `notifications.models.Notification` (aka Activity Notifications)
    and then send Real Time Notifications through Redis to the recipient

    :param actor: The actor from `notifications.models.Notification`
    :param recipient: The recipient of the notification
    :param verb: The verb from `notifications.models.Notification`
    :param target: the target from `notifications.models.Notification`
    :param action_object: the action_object from `notifications.models.Notification`
    :param render_string: the render_string inserted in the data field in `notifications.models.Notification`
            Used for properly rendering the notifications to the user
    :param transient: If the notification will be stored or not
    :param created: float timestamp
    :return: True/False
    """
    from core.tools import notification_url
    actor = User.objects.get(id=actor_id)
    recipient = User.objects.get(id=recipient_id)
    if target_type == "User":
        target = User.objects.get(id=target_id)
    elif target_type == "Document":
        target = Document.objects.get(id=target_id)
    elif target_type == "Sentence":
        target = Sentence.objects.get(id=target_id)
    else:
        target = None

    action_object = None
    if action_object_type == "Document":
        action_object = Document.objects.get(id=action_object_id)
    elif action_object_type == "Sentence":
        action_object = Sentence.objects.get(id=action_object_id)

    logging.info('store_activity_notification: actor=%s, recipient=%s, '
                 'verb=%s, target=%s, action_object=%s, render_string=%s' % (
                     str(actor), str(recipient), str(verb), str(target), str(action_object), render_string))

    notification = Notification()
    notification.actor = actor
    notification.recipient = recipient
    notification.verb = verb
    notification.target = target
    notification.action_object = action_object
    if created is not None:

        if isinstance(created, float) or isinstance(created, int):
            try:
                created = datetime.utcfromtimestamp(created)
                created = created.replace(tzinfo=pytz.utc)
                created = timezone.localtime(created)
            except Exception:
                logging.error('store_activity_notification: probably malformed timestamp: %s', str(created))
                created = None

        notification.timestamp = created

    data = {}
    if render_string is not None:
        data['render_string'] = render_string

    data['transient'] = transient

    if data:
        notification.data = data

    if not transient:
        notification.save()

    notif_dict = notification_to_dict(notification)
    notif_dict['url'] = notification_url(notification)

    NotificationManager.create_user_message(recipient,
                                            event_name='message',
                                            message={'notif': NotificationManager.ServerNotifications.ACTIVITY_UPDATE,
                                                     'activity_update': notif_dict}).send()

    return notification.pk


@shared_task
def mark_as_read_sentence_related_notifications(user_id, sentence_id):
    sentence_ctype = ContentType.objects.get_for_model(Sentence).pk

    sentence = Sentence.objects.get(pk=sentence_id)
    sentence_versions = Sentence.objects.filter(uuid=sentence.uuid)

    for sentence_instance in sentence_versions:
        has_recipient = Q(recipient=user_id)
        relates_to_sentence = Q(action_object_object_id=sentence_instance.pk,
                                action_object_content_type=sentence_ctype) | \
                              Q(target_object_id=sentence_instance.pk,
                                target_content_type=sentence_ctype)
        Notification.objects.filter(has_recipient & relates_to_sentence).update(unread=False)

    fully_refresh_persistent_notifications.delay(user_id)


@shared_task
def fully_refresh_persistent_notifications(recipient_id):
    recipient = User.objects.get(id=recipient_id)
    NotificationManager.create_user_message(recipient,
                                            event_name='message',
                                            message={
                                                'notif': NotificationManager.ServerNotifications.NOTIFICATIONS_FULL_UPDATE}).send()


# Import all the periodic tasks
import core.cron
