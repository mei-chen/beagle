import requests

from django.conf import settings
import json


class MostSimilarModelAPI(object):

    def __init__(self, word, model):
        self.word = word
        self.model = model

    def _build_url(self):
        return settings.MOST_SIMILAR_ENDPOINT.format(**{
            'word': self.word,
            'model': self.model,
            'number': settings.MOST_SIMILAR_DEFAULT_NUMBER,
            'user': settings.MOST_SIMILAR_USER,
            'password': settings.MOST_SIMILAR_PASSWORD
        })

    def _make_request(self):
        return requests.get(self._build_url())

    def process(self):
        response = self._make_request()

        if response.ok:
            return (
                True,
                'Successfully acquired recommendations for {}'.format(self.word),
                json.loads(response.json())
            )
        else:
            try:
                message = response.json()['error']
            except (ValueError, KeyError):
                message = 'An error occurred. Status: {}'.format(response.status_code)
            return False, message, []
