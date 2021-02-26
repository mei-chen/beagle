import logging

from celery import shared_task

from beagle_bot.bot import BeagleBot
from beagle_realtime.notifications import NotificationManager


@shared_task
def ask_beagle(question, sentence, sentence_idx, document):
    from core.models import Sentence
    logging.info("Celery: starting `ask_beagle` question=%s" % question)
    comment_dict, response_type = BeagleBot.ask(question)

    # Get a fresh copy of the sentence
    sentence = Sentence.objects.get(pk=sentence.pk)

    comment_dict = Sentence.expand_comment_dict(
        sentence.add_beaglebot_comment(comment_dict, response_type),
        sentence, document
    )

    notification_payload = {
        'comment': comment_dict,
        'notif': NotificationManager.ServerNotifications.COMMENT_ADDED_NOTIFICATION,
        'sentence': sentence.to_dict(),
    }
    notification_payload['sentence']['idx'] = sentence_idx

    NotificationManager.create_document_message(document, 'message',
                                                notification_payload).send()
    logging.info("Celery: finished `ask_beagle` question=%s" % question)
    return True
