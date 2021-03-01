import json
import logging
import re

from rest_framework.response import Response
from rest_framework.views import APIView

from analysis.models import Report
from analysis.tasks import synonyms_recommend, pull_similar_sentences
from portal.models import Batch, Sentence
from utils.synonyms.api import SynonymsAPI

logger = logging.getLogger(__name__)


class RecommendSynonyms(APIView):

    def post(self, request):
        word = request.data['word'].strip()
        synonyms_recommend.delay(word, request.session.session_key)

        return Response()


class PullSimilarSentences(APIView):

    def post(self, request):
        pull_similar_sentences.delay(sentence=request.data['sentence'],
                                     batch_id=request.data['batch'],
                                     session_key=request.session.session_key)

        return Response()


class AggregatedSentencesSearch(APIView):

    def get(self, request):
        text = request.query_params['text']
        batch = Batch.objects.get(id=request.query_params['batch'])
        profile = request.user.profile

        if request.query_params.get('type') == 'rgx':
            payload = filter_sentences_by_rgx(text, batch)

        elif len(text.split()) > profile.sentence_word_threshold:
            payload = filter_similar_sentences(text, batch, profile)

        else:
            payload = filter_sentences_by_word(text, batch)

        return Response(payload)


def filter_sentences_by_rgx(rgx, batch):
    result = []
    sentences = Sentence.objects.filter(
        document__source_file__batch=batch)
    compiled_regex = re.compile(rgx)

    for sent in sentences:
        if compiled_regex.search(sent.text):
            result.append({
                'text': sent.text,
                'id': sent.id,
                'match': rgx
            })

    for data in result:
        data.update(
            get_sentence_context(data['id'], sentences)
        )

    return result


def filter_similar_sentences(sent, batch, profile):
    result = []
    report = Report(batch=batch).pull_similar_sentences(sent)
    for entry in json.loads(report.json):
        if float(entry['score']) > profile.min_similarity_score:
            result.append({
                'text': entry['sentence'],
                'id': int(entry['sent_id']),
                'match': sent
            })
    report.delete()

    sentences = Sentence.objects.filter(document__source_file__batch=batch)
    for data in result:
        data.update(
            get_sentence_context(data['id'], sentences)
        )

    return result


def filter_sentences_by_word(word, batch):
    result = []
    sentences = Sentence.objects.filter(
        document__source_file__batch=batch)
    api = SynonymsAPI(word)
    success, message, response = api.process()
    if not success:
        logger.error('SynonymsAPI: %s' % message)

    if response:
        keywords = response.get('synonyms', [])[:5]
    else:
        keywords = []

    keywords.append(word)

    keywords_regexs = {
        keyword: re.compile(u'\\b{}\\b'.format(re.escape(keyword)),
                   re.IGNORECASE | re.UNICODE) for keyword in keywords
    }

    for sent in sentences:
        for keyword, regex in keywords_regexs.items():
            if regex.search(sent.text):
                result.append({
                    'text': sent.text,
                    'id': sent.id,
                    'match': keyword
                })
                break # One match per sentence is enough

    for data in result:
        data.update(
            get_sentence_context(data['id'], sentences)
        )

    return result


def get_sentence_context(id, sents):
    context = {
        'nearby_sentences': []
    }

    sent = Sentence.objects.get(id=id)
    nearby_sents_ids = [id - 2, id - 1, id + 1, id + 2]
    for id in nearby_sents_ids:
        if sents.filter(id=id) and sents.get(id=id).document == sent.document:
            context['nearby_sentences'].append(sents.get(id=id).text)

    return context