import logging
import requests


class SlackPostAPI:
    def __init__(self, webhook, default_channel=None, default_username=None, default_icon_emoji=None):
        self.webhook = webhook
        self.default_channel = default_channel
        self.default_username = default_username
        self.default_icon_emoji = default_icon_emoji

    def send_message(self, message, **kwargs):
        data = {
            'text': message,
            'channel': kwargs.get('channel', self.default_channel),
            'username': kwargs.get('username', self.default_username),
            'icon_emoji': kwargs.get('icon_emoji', self.default_icon_emoji)
        }
        logging.info('slack sending message: "%s" to channel: "%s"' % (message, data['channel']))
        response = requests.post(self.webhook, json=data)
        logging.info('slack message response %s: %s' % (response.status_code, response.text))