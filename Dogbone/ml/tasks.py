import logging
import os
import redis
import redis_lock
import requests

from celery import shared_task
from constance import config
from django.conf import settings

from ml.capsules import Capsule
from ml.facade import LearnerFacade


@shared_task
def onlinelearner_train_task(tag, user, sentence, s_idx):
    logging.info("Celery: starting `onlinelearner train task` sentence_uuid=%s" % sentence.uuid)

    document = sentence.doc
    if not document.is_ready:
        return False

    # Train the appropriate Online Learner
    conn = redis.StrictRedis.from_url(settings.REDIS_URL)
    with redis_lock.Lock(conn, 'OL_%s_%s' % (tag, user.username)):
        ofcd = LearnerFacade.get_or_create(tag, user)
        capsules = [Capsule(sentence.text, idx=s_idx, parties=document.get_parties())]
        labels = [True]
        all_capsules = [(Capsule(s.text), s.get_tags()) for s in document.get_sorted_sentences()]
        ofcd.train(capsules, labels, infer_negatives=True, all_capsules=all_capsules)

    logging.info("Celery: finished `onlinelearner train task` sentence_uuid=%s" % sentence.uuid)

    return True


@shared_task
def onlinelearner_removesample_task(tag, user, sentence, s_idx):
    logging.info("Celery: starting `onlinelearner removesample task` sentence_uuid=%s" % sentence.uuid)

    document = sentence.doc
    if not document.is_ready:
        return False

    # Get the appropriate Online Learner
    conn = redis.StrictRedis.from_url(settings.REDIS_URL)
    with redis_lock.Lock(conn, 'OL_%s_%s' % (tag, user.username)):
        olearner = LearnerFacade.get_or_create(tag, user)
        capsule = Capsule(sentence.text, idx=s_idx, parties=document.get_parties())
        olearner.remove_sample(capsule)

    logging.info("Celery: finished `onlinelearner removesample task` sentence_uuid=%s" % sentence.uuid)

    return True


@shared_task
def onlinelearner_negative_train_task(tag, user, sentence, s_idx):
    logging.info("Celery: starting `onlinelearner negative train task` sentence_uuid=%s" % sentence.uuid)

    document = sentence.doc
    if not document.is_ready:
        return False

    # Train the appropriate Online Learner
    conn = redis.StrictRedis.from_url(settings.REDIS_URL)
    with redis_lock.Lock(conn, 'OL_%s_%s' % (tag, user.username)):
        ofcd = LearnerFacade.get_or_create(tag, user)
        capsules = [Capsule(sentence.text, idx=s_idx, parties=document.get_parties())]
        labels = [False]
        ofcd.train(capsules, labels)

    logging.info("Celery: finished `onlinelearner negative train task` sentence_uuid=%s" % sentence.uuid)

    return True


@shared_task
def spot_experiment_accept_sentence(tag, experiment_uuid, sentence, sentence_idx):
    logging.info('Starting: accept sentence=%s by Spot experiment=%s',
                 sentence.uuid, experiment_uuid)

    document = sentence.doc
    if not document.is_ready:
        return False

    parties = document.get_parties()

    text = Capsule(sentence.text, parties=parties).preprocess()
    label = True

    capsules = [Capsule(sentence.text, idx=sentence_idx, parties=parties)]
    labels = [label]
    all_capsules = [(Capsule(s.text), s.get_tags())
                    for s in document.get_sorted_sentences()]

    infered_negative_capsules = \
        LearnerFacade.infer_negatives_global(tag, capsules, labels, all_capsules)
    infered_negatives = [nsc.text for nsc in infered_negative_capsules]

    user_profile = document.owner.details
    spot_access_token = user_profile.spot_access_token

    # Actual names of dogbone tags don't make sense in Spot,
    # so simply use the username of the document's owner
    tag = document.owner.username

    url = os.path.join(config.SPOT_API_URL, 'publish',
                       experiment_uuid, 'add_sample') + '/'
    data = {'tag': tag, 'text': text, 'label': label,
            'infered_negatives': infered_negatives}
    headers = {'X-Access-Token': spot_access_token}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 403:
        logging.warning('Could not access Spot API due to failed authentication. '
                        'Make sure to authorize your account in Spot.')

    if response.status_code == 404:
        logging.warning('Removing experiment=%s since it does not exist in Spot anymore.',
                        experiment_uuid)
        user_profile.pop_spot_experiment(experiment_uuid)

    if response.status_code == 200:
        logging.info('Accepted successfully!')

    logging.info('Finished: accept sentence=%s by Spot experiment=%s',
                 sentence.uuid, experiment_uuid)

    return True


@shared_task
def spot_experiment_reject_sentence(experiment_uuid, sentence):
    logging.info('Starting: reject sentence=%s by Spot experiment=%s',
                 sentence.uuid, experiment_uuid)

    document = sentence.doc
    if not document.is_ready:
        return False

    parties = document.get_parties()

    text = Capsule(sentence.text, parties=parties).preprocess()
    label = False

    user_profile = document.owner.details
    spot_access_token = user_profile.spot_access_token

    # Actual names of dogbone tags don't make sense in Spot,
    # so simply use the username of the document's owner
    tag = document.owner.username

    url = os.path.join(config.SPOT_API_URL, 'publish',
                       experiment_uuid, 'add_sample') + '/'
    data = {'tag': tag, 'text': text, 'label': label}
    headers = {'X-Access-Token': spot_access_token}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 403:
        logging.warning('Could not access Spot API due to failed authentication. '
                        'Make sure to authorize your account in Spot.')

    if response.status_code == 404:
        logging.warning('Removing experiment=%s since it does not exist in Spot anymore.',
                        experiment_uuid)
        user_profile.pop_spot_experiment(experiment_uuid)

    if response.status_code == 200:
        logging.info('Rejected successfully!')

    logging.info('Finished: reject sentence=%s by Spot experiment=%s',
                 sentence.uuid, experiment_uuid)

    return True
