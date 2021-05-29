import requests
import json
from django.conf import settings


class SynonymsAPI(object):

    def __init__(self, word):
        self.word = word

    def _make_request(self):
        # headers = {
        #     'X-Mashape-Key': settings.SYNONYMS_API_KEY,
        #     'Accept': 'application/json'
        # }
        return requests.get(
            settings.SYNONYMS_ENDPOINT.format(word=self.word),
            #headers=headers
        )

    def process(self):
        response = self._make_request()

        if response.ok:
            return (
                True,
                'Successfully acquired synonyms for {}'.format(self.word),
                json.loads(response.json())
            )
        else:
            try:
                message = response.json()['error']
            except (ValueError, KeyError):
                message = 'An error occurred. Status: {}'.format(response.status_code)
            return False, message, []
