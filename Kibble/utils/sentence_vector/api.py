import numpy as np
import requests
import json

from django.conf import settings
from django.template.defaultfilters import pluralize


class SentenceVectorAPIError(Exception):
    pass


class SentenceVectorAPI(object):

    def __init__(self, sentence_or_sentences):
        self.sentences = sentence_or_sentences
        self.singleton = False

        if not isinstance(self.sentences, list):
            self.sentences = [self.sentences]
            self.singleton = True

    def _get_payload(self):
        return {
            'sentences': self.sentences,
            'model': settings.SENTENCE_VECTOR_DEFAULT_MODEL,
            'algorithm': settings.SENTENCE_VECTOR_DEFAULT_ALGORITHM,
            'alpha': settings.SENTENCE_VECTOR_DEFAULT_ALPHA,
            'user': settings.SENTENCE_VECTOR_USER,
            'password': settings.SENTENCE_VECTOR_PASSWORD
        }

    def _make_request(self):
        headers = {
            'Content-Type': 'application/json'
        }
        return requests.post(
            settings.SENTENCE_VECTOR_ENDPOINT,
            json=self._get_payload(),
            headers=headers
        )

    def _np_array_from_str(self, str_array):
        # Expected raw format: '[ 1 2 3 ]'
        return np.array(str_array.strip('[]').split()).astype(float)

    def _post_process(self, payload):
        payload['vectors'] = list(map(self._np_array_from_str, payload['vectors']))
        return payload

    def process(self):
        response = self._make_request()

        if response.ok:
            return (
                True,
                'Successfully vectorized {} sentence{}'.format(
                    len(self.sentences), pluralize(len(self.sentences))
                ),
                self._post_process(json.loads(response.json()))
            )
        else:
            try:
                message = response.json()['error']
            except (ValueError, KeyError):
                message = 'An error occurred. Status: {}'.format(response.status_code)
            return False, message, []

    def vectorize(self):
        success, message, result = self.process()
        vectors = result.get('vectors') if success else None
        return (vectors[0]
                if vectors is not None and self.singleton else
                vectors)
