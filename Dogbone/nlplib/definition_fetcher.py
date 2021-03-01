import csv
import os

import wikipedia


class BlacksDictionaryDefinitionFetcher(object):

    _BLACKS_DICT_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources', 'blacks_second_edition_terms.csv'
    )

    _BLACKS_DICT = None

    @classmethod
    def _initialize(cls):
        if cls._BLACKS_DICT is None:
            with open(cls._BLACKS_DICT_PATH) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                cls._BLACKS_DICT = {
                    term.lower(): definition for term, definition in csv_reader
                }

    @classmethod
    def find_definition(cls, term):
        # Lazy initialization
        cls._initialize()

        definition = cls._BLACKS_DICT.get(term.lower())

        if definition is None:
            return None

        return {
            'title': term.title(),
            'definition': definition
        }


class WikipediaDefinitionFetcher(object):

    @staticmethod
    def _get_best_search_result(query):
        return wikipedia.search(query)[0]

    @staticmethod
    def _suggest_correction(query):
        return wikipedia.suggest(query)

    @staticmethod
    def _get_page(title):
        try:
            return wikipedia.page(title)
        except wikipedia.exceptions.DisambiguationError:
            return None

    @classmethod
    def find_definition(cls, query, suggest_correction=True):
        if suggest_correction:
            suggestion = cls._suggest_correction(query)
            if suggestion is not None:
                query = suggestion

        title = cls._get_best_search_result(query)
        page = cls._get_page(title)

        if page is None:
            return None

        return {
            'title': title,
            'definition': page.summary
        }
