#!/usr/bin/python

import sys
import email
import validators
import logging
import syslog
import logging.handlers
from email.utils import parseaddr
from commands import RufusCommandDispatcher

# Project
from incoming.models import User as SenderUser

logger = logging.getLogger(__name__)


#######################################################################################################################
#
# Main routine
#
#######################################################################################################################

def main_sample(message, email_domain):
    from api import InternalAPI

    api = InternalAPI(email_domain)
    fullname, from_address = parseaddr(message.get('From'))
    if not validators.email(from_address):
        return

    api.ping_server(from_address)


def main(message, email_domain, content):
    syslog.syslog("Starting `def main(message, %s)`" % email_domain)

    from api import InternalAPI
    try:
        api = InternalAPI(email_domain)
        fullname, from_address = parseaddr(message.get('From'))
        sender = SenderUser.create_user(name=fullname, email=from_address, domain=email_domain)
        sender.save_email_content(content)

        if not validators.email(from_address):
            sender.response = 'Email not validated'
            sender.success = False
            sender.save()
            return

        user = api.get_user(from_address)
        if not user:
            user = api.create_user(from_address)

        # If the user couldn't be created, exit
        if user is None:
            logger.error("The user could not be created. email=%s" % from_address)
            sender.success = False
            sender.response = "The user could not be created. email=%s" % from_address
            sender.save()
            # TODO: Report to the person that the document could not be processed
            return

        if not user['is_paid'] and not user['had_trial']:
            subscription = api.create_subscription(user_addr=from_address)
            if subscription is None:
                logger.error("Could not create subscription for user=%s" % from_address)
                sender.success = False
                sender.response = "Could not create subscription for user=%s" % from_address
                sender.save()
                return

        command_dispatcher = RufusCommandDispatcher(message, email_domain, sender=sender)
        response = command_dispatcher.dispatch()

        # As this is not mission critical incase it fails, don't do anything
        try:
            if response.get('document_id'):  # If document id has been set assume success
                sender.success = True
            else:
                sender.success = False
            sender.save()


            sender.response = unicode(response)
            sender.save()

        except Exception as e:
            sender.success = False
            sender.response = str(e)
            sender.save()
            logger.error("Exception occurred: %s" % str(e))

    except Exception as e:
        sender.success = False
        sender.response = str(e)
        sender.save()
        import traceback
        print traceback.format_exc()
        logger.error("Exception occurred: %s" % str(e))


def get_module_name():
    return __name__


def read_input():
    return sys.stdin.read()


def call_main():
    if get_module_name() == "__main__":
        try:
            content = read_input()
            msg = email.message_from_string(content)
            env = sys.argv[1].upper()
        except Exception as e:
            logger.error("Could not read message or build email message: %s" % str(e))

        main(msg, env)

call_main()
