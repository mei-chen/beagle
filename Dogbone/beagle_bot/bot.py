from nlplib.definition_fetcher import (
    BlacksDictionaryDefinitionFetcher,
    WikipediaDefinitionFetcher,
)
from . import LuisAPI


class BeagleBot:
    username = '@beagle'

    class ResponseTypes:
        ERROR = 'error'
        WIKIPEDIA = 'wiki_response'
        BLACKS = 'blacks_definition'

    @classmethod
    def ask(cls, question):
        """
        :param question: The actual question for beagle bot (stripped of unnecessary mentions)
        :return: The extended comment dict
        """

        question = question.strip()
        subject, score = LuisAPI.ask(question)

        comment_dict = {'title': None, 'body': None, 'status': 0}

        if subject and score > LuisAPI.MIN_LUIS_CONFIDENCE:
            result = BlacksDictionaryDefinitionFetcher.find_definition(subject)
            if result:
                response_type = BeagleBot.ResponseTypes.BLACKS
            else:
                result = WikipediaDefinitionFetcher.find_definition(subject)
                response_type = BeagleBot.ResponseTypes.WIKIPEDIA

            if result is None:
                comment_dict['status'] = 1
                comment_dict['title'] = "Sorry, Beagle is still a puppy in training"
                response_type = BeagleBot.ResponseTypes.ERROR
            else:
                comment_dict['title'] = result['title']
                comment_dict['body'] = result['definition']

        else:
            comment_dict['status'] = 1
            comment_dict['title'] = "Sorry, the question seems a bit ambiguous ..."
            response_type = BeagleBot.ResponseTypes.ERROR

        return comment_dict, response_type
