import os
import re
import requests

from django.conf import settings


class SentenceSplittingRemoteAPI(object):

    _WHITESPACE_SEQUENCE_RE = re.compile(r'\s+', re.UNICODE)

    def __init__(self, file):
        self.file = file

    def _get_payload(self):
        self.file.seek(0)
        payload = {
            'text': self.file.read()
        }
        self.file.seek(0)
        return payload

    def _make_request(self):
        headers = {
            'X-Access-Token': settings.SENTENCE_SPLITTING_TOKEN,
            'Content-Type': 'application/json'
        }
        return requests.post(
            settings.SENTENCE_SPLITTING_ENDPOINT,
            json=self._get_payload(),
            headers=headers
        )

    def _compress_whitespaces(self, sentence):
        return self._WHITESPACE_SEQUENCE_RE.sub(' ', sentence).strip()

    def _post_process(self, payload):
        return map(self._compress_whitespaces, payload)

    def process(self):
        response = self._make_request()

        if response.ok:
            return (
                True,
                'Successfully split sentences from {}'.format(
                    os.path.basename(self.file.name)
                ),
                self._post_process(response.json())
            )
        else:
            try:
                message = response.json()['error']
            except (ValueError, KeyError):
                message = 'An error occurred. Status: {}'.format(response.status_code)
            return False, message, []

    def process_text(self, text):
        headers = {
            'X-Access-Token': settings.SENTENCE_SPLITTING_TOKEN,
            'Content-Type': 'application/json'
        }
        response = requests.post(
            settings.SENTENCE_SPLITTING_ENDPOINT,
            json={'text': text},
            headers=headers
        )

        if response.ok:
            return True, self._post_process(response.json())
        else:
            try:
                m = response.json()['error']
            except (ValueError, KeyError):
                m = 'An error occurred. Status: {}'.format(response.status_code)
            return False, m
