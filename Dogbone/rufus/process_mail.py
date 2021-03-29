#!/usr/bin/python

import sys
import email
import validators
import logging
import logging.handlers
from email.utils import parseaddr
from commands import RufusCommandDispatcher

logger = logging.getLogger('RufusLogger')


#######################################################################################################################
#
# Main routine
#
#######################################################################################################################

def main(message, current_env):
    from api import InternalAPI
    try:
        api = InternalAPI(current_env)
        fullname, from_address = parseaddr(message.get('From'))
        if not validators.email(from_address):
            return

        user = api.get_user(from_address)

        if not user:
            user = api.create_user(from_address)

        # If the user couldn't be created, exit
        if user is None:
            logger.error("The user could not be created. email=%s" % from_address)
            # TODO: Report to the person that the document could not be processed
            return

        if not user['is_paid'] and not user['had_trial']:
            subscription = api.create_subscription(user_addr=from_address)
            if subscription is None:
                logger.error("Could not create subscription for user=%s" % from_address)
                return

        command_dispatcher = RufusCommandDispatcher(message, current_env)
        command_dispatcher.dispatch()

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        logger.error("Exception occurred: %s" % str(e))


# def main(message, current_env):
#     try:
#         from_field = message.get('From')
#         from_addr = extract_addr(from_field)
#         subject = message.get('Subject')
#
#         logger.info("Incoming email from=%s subject=%s" % (from_addr, subject))
#
#         api = InternalAPI(current_env)
#
#         attachments = get_attachments(message, api, from_addr)
#         logger.info("Attachment files=%s", str(attachments))
#
#         user = api.get_user(from_addr)
#         logger.info("User payload: %s", str(user))
#
#
#         # Try to create the user
#         if user is None:
#             user = api.create_user(from_addr)
#
#             # If we still couldn't create the user, exit
#             if user is None:
#                 # TODO: Report to the person that the document could not be processed
#                 logger.error("The user could not be created. email=%s" % from_addr)
#                 exit()
#
#         if not user['is_paid'] and not user['had_trial']:
#             subscription = api.create_subscription(user_addr=from_addr)
#             if subscription is None:
#                 logger.error("Could not create subscription for user=%s" % from_addr)
#                 exit()
#
#         # For now, upload the document for every one
#         # TODO: if the user is not paid and the user had the trial, don't upload a document and send appropriate response
#         if attachments:
#             api.upload_document(from_addr, attachments)
#
#     except Exception as e:
#         import traceback
#         print traceback.format_exc()
#         logger.error("Exception occurred: %s" % str(e))

#######################################################################################################################
#
# Calls
#
#######################################################################################################################

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