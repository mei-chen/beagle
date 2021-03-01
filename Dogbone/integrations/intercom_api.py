# ~*~ coding: utf-8 ~*~
import logging
import requests
from requests.auth import HTTPBasicAuth


class IntercomAPI:

    MESSAGES_ENDPOINT = 'https://api.intercom.io/messages'

    def __init__(self, app_id, api_key):
        self.APP_ID, self.API_KEY = app_id, api_key

    @classmethod
    def build_inapp_json(cls, from_id, to_email, message):
        """
        Build an intercom formatted json for sending an inapp message
        :param from_id: The user sending the message
        :param to_email: The application user receiving the message
        :param message: The actual message
        :return:
        """
        return {
            'message_type': 'inapp',
            'body': message,
            'from': {
                'type': 'admin',
                'id': str(from_id)
            },
            'to': {
                'type': 'user',
                'email': to_email
            }
        }

    def send_message(self, from_id, to_email, message):
        """
        Send an intercom `message` from the intercom user `from_id` to the application user `to_email`
        :param from_id: The user sending the message
        :param to_email: The application user receiving the message
        :param message: The actual message
        :return:
        """
        logging.info('Sending Intercom message: %s to %s' % (message, to_email))
        intercom_json = IntercomAPI.build_inapp_json(from_id, to_email, message)
        intercom_headers = {
            'Accept': 'application/json'
        }

        try:
            r = requests.post(IntercomAPI.MESSAGES_ENDPOINT,
                              json=intercom_json,
                              headers=intercom_headers,
                              auth=HTTPBasicAuth(self.APP_ID, self.API_KEY))

            logging.info('intercom API response [%s] %s' % (r.status_code, r.text))
            return True

        except Exception as e:
            logging.error(
                'intercom API message failed [%s] %s' % (
                    type(e).__name__, str(e)
                )
            )

        return False
