import json
import logging
from urllib.request import Request, urlopen, URLError, quote


class LUIS:

    MIN_LUIS_CONFIDENCE = 0.5

    def __init__(self, base_url=None):
        self.base_url = base_url or 'https://api.projectoxford.ai/luis/v1/application?id=ef8b459c-874d-4164-8833-7b2bf8a9ae13&subscription-key=ec51008c54ec41aeb2d0197e847a175c'

    def ask(self, question):
        data = self.generic_query(question)
        if data is None:
            return None, None
        entities = data['entities']
        intents = data['intents']
        meaning = 0.
        for i in intents:
            if i['intent'] == 'Find meaning':
                meaning = i['score']
        subject = None
        for e in entities:
            if e['type'] == 'Subject':
                subject = e['entity']
        return subject, meaning

    def generic_query(self, q):
        request = Request(self.base_url + '&q=' + quote(q))
        try:
            response = urlopen(request)
            data = json.load(response)
            return data
        except URLError as e:
            logging.critical('Could not access Luis API: %s', e)
            return None


if __name__ == '__main__':
    luis = LUIS()
    print(luis.ask('Is a responsibility actually a right denial?'))
