import csv
import json
import numpy as np
import random
import re
import uuid

from io import StringIO
from sklearn.metrics.pairwise import cosine_similarity

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.template.defaultfilters import truncatechars
from django.contrib.auth.models import User

from analysis.constants import ReportTypes
from document.models import Sentence
from portal.models import Batch
from utils.sentence_vector.api import SentenceVectorAPI, SentenceVectorAPIError


RANDOM_STATE = 42


class SimModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, unique=True)
    api_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class RegEx(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, unique=True)
    content = models.CharField(max_length=4096)
    owner = models.ForeignKey(User, null=True, blank=True,
                              related_name='regexes',on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class Report(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    batch = models.ForeignKey(Batch, related_name='reports', on_delete=models.CASCADE)
    json = models.TextField(default=json.dumps([]))
    name = models.CharField(max_length=4096)
    report_type = models.SmallIntegerField(choices=ReportTypes.choices())

    class Meta:
        ordering = ['-id']

    def apply_regex(self, regex):
        sentences = Sentence.objects.filter(
            document__source_file__batch=self.batch
        )
        compiled_regex = re.compile(regex.content)

        result = []
        for sent in sentences:
            for match_obj in compiled_regex.finditer(sent.text):
                point = match_obj.group()
                row = {
                    'batch': self.batch.name,
                    'regex': regex.name,
                    'sentence': sent.text,
                    'found': point
                }
                if row not in result:
                    result.append(row)

        if not result:
            return None

        self.name = 'Report {} for {}'.format(self.batch.name, regex.name)
        self.json = json.dumps(result)
        self.report_type = ReportTypes.RegEx.value
        self.save()
        return self

    def apply_regex_negative(self, regex):
        """
        Applies regex in negative pattern, returns sentences WITHOUT mentioned
        pattern. Returns no more than 2 * number of sentences WITH pattern.
        """
        sentences = Sentence.objects.filter(
            document__source_file__batch=self.batch
        )
        compiled_regex = re.compile(regex.content)

        matched_sents_count = 0

        result = []
        for sent in sentences:
            # Try find any match, no need to find all matches
            match_obj = compiled_regex.search(sent.text)
            if match_obj:
                matched_sents_count += 1
            row = {
                'batch': self.batch.name,
                'regex': regex.name,
                'sentence': sent.text
            }
            if not match_obj and row not in result:
                result.append(row)

        if not result:
            return None

        result = result[: 2 * matched_sents_count]

        self.name = 'Negative Report {} for {}'.format(self.batch.name, regex.name)
        self.json = json.dumps(result)
        self.report_type = ReportTypes.RegEx.value
        self.save()
        return self

    @staticmethod
    def _skip_sentence(sent, stop_words_regexs):
        return any(regex.search(sent.text)
                   for regex in stop_words_regexs.values())

    def apply_keyword(self, keywordlist, stop_words):
        sentences = Sentence.objects.filter(
            document__source_file__batch=self.batch
        )
        keywords = keywordlist.keywords.all()
        keywords_regexs = {
            keyword: re.compile(u'\\b{}\\b'.format(re.escape(keyword.content)),
                                re.IGNORECASE | re.UNICODE)
            for keyword in keywords
        }
        stop_words_regexs = {
            stop_word: re.compile(u'\\b{}\\b'.format(re.escape(stop_word)),
                                  re.IGNORECASE | re.UNICODE)
            for stop_word in stop_words
        }

        sentences = [sent for sent in sentences
                     if not self._skip_sentence(sent, stop_words_regexs)]

        result = []
        for sent in sentences:
            for keyword, regex in keywords_regexs.items():
                if regex.search(sent.text):
                    row = {
                        'batch': self.batch.name,
                        'keywordlist': keywordlist.name,
                        'keyword': keyword.content,
                        'sentence': sent.text
                    }
                    if row not in result:
                        result.append(row)

        if not result:
            return None

        self.name = 'Report {} for {}'.format(self.batch.name, keywordlist.name)
        self.json = json.dumps(result)
        self.report_type = ReportTypes.KeyWord.value
        self.save()
        return self

    def apply_keyword_negative(self, keywordlist, stop_words):
        """
        Applies keywords in negative pattern, returns sentences WITHOUT mentioned
        keywords. Returns no more than 2 * number of sentences WITH keywords.
        """
        sentences = Sentence.objects.filter(
            document__source_file__batch=self.batch
        )
        keywords = keywordlist.keywords.all()
        keywords_regexs = {
            keyword: re.compile(u'\\b{}\\b'.format(re.escape(keyword.content)),
                                re.IGNORECASE | re.UNICODE)
            for keyword in keywords
        }
        stop_words_regexs = {
            stop_word: re.compile(u'\\b{}\\b'.format(re.escape(stop_word)),
                                  re.IGNORECASE | re.UNICODE)
            for stop_word in stop_words
        }

        sentences = [sent for sent in sentences
                     if not self._skip_sentence(sent, stop_words_regexs)]

        keywords_allowed_sents_counts = {keyword: 0
                                         for keyword in keywords}

        for sent in sentences:
            for keyword, regex in keywords_regexs.items():
                if regex.search(sent.text):
                    keywords_allowed_sents_counts[keyword] += 2

        result = []
        for sent in sentences:
            for keyword, regex in keywords_regexs.items():
                if not keywords_allowed_sents_counts[keyword]:
                    continue
                if not regex.search(sent.text):
                    row = {
                        'batch': self.batch.name,
                        'keywordlist': keywordlist.name,
                        'keyword': keyword.content,
                        'sentence': sent.text
                    }
                    if row not in result:
                        result.append(row)
                        keywords_allowed_sents_counts[keyword] -= 1

        if not result:
            return None

        self.name = 'Negative Report {} for {}'.format(self.batch.name, keywordlist.name)
        self.json = json.dumps(result)
        self.report_type = ReportTypes.KeyWord.value
        self.save()
        return self

    @staticmethod
    def _calculate_groups_sizes():
        return {
            group: int(settings.SENTENCE_PULL_SIZE * (percentage / 100.))
            for group, percentage in zip(
                ['high', 'medium', 'low'], settings.SENTENCE_PULL_PERCENTAGES
            )
        }

    @staticmethod
    def _initialize_sentences_by_groups():
        return {group: [] for group in ['high', 'medium', 'low']}

    def pull_similar_sentences(self, sentence):
        vector = SentenceVectorAPI(sentence).vectorize()
        if vector is None:
            raise SentenceVectorAPIError

        vector = np.array(vector).astype(float)

        sentences = Sentence.objects.filter(
            document__source_file__batch=self.batch
        )
        vectors = [s.vector for s in sentences]
        scores = cosine_similarity(
            vector.reshape((1, -1)), np.array(vectors)
        ).ravel()
        # Convert [-1, 1] to [1, 5]
        scores = 2 * scores + 3

        # Keep track of how many sentences are left to pull in each group
        groups_sizes = self._calculate_groups_sizes()

        sentences_by_groups = self._initialize_sentences_by_groups()
        for index, score in enumerate(scores):
            if score > 4:
                group = 'high'
            elif score > 3:
                group = 'medium'
            else:
                group = 'low'
            sentences_by_groups[group].append(index)

        random.seed(RANDOM_STATE)

        for group in sentences_by_groups:
            random.shuffle(sentences_by_groups[group])

        pulled_sentences_by_groups = self._initialize_sentences_by_groups()

        if len(sentences_by_groups['high']) >= groups_sizes['high']:
            pulled_sentences_by_groups['high'] = \
                sentences_by_groups['high'][:groups_sizes['high']]
            sentences_by_groups['high'] = \
                sentences_by_groups['high'][groups_sizes['high']:]
        else:
            pulled_sentences_by_groups['high'] = sentences_by_groups['high']
            groups_sizes['medium'] += \
                groups_sizes['high'] - len(sentences_by_groups['high'])
            sentences_by_groups['high'] = []

        groups_sizes['high'] = 0

        if len(sentences_by_groups['medium']) >= groups_sizes['medium']:
            pulled_sentences_by_groups['medium'] = \
                sentences_by_groups['medium'][:groups_sizes['medium']]
            sentences_by_groups['medium'] = \
                sentences_by_groups['medium'][groups_sizes['medium']:]
            groups_sizes['medium'] = 0
        else:
            pulled_sentences_by_groups['medium'] = sentences_by_groups['medium']
            groups_sizes['medium'] -= len(sentences_by_groups['medium'])
            sentences_by_groups['medium'] = []

        if len(sentences_by_groups['low']) >= groups_sizes['low']:
            pulled_sentences_by_groups['low'] = \
                sentences_by_groups['low'][:groups_sizes['low']]
            sentences_by_groups['low'] = \
                sentences_by_groups['low'][groups_sizes['low']:]
            groups_sizes['low'] = 0
        else:
            pulled_sentences_by_groups['low'] = sentences_by_groups['low']
            groups_sizes['low'] -= len(sentences_by_groups['low'])
            sentences_by_groups['low'] = []

        result = []
        for group in pulled_sentences_by_groups:
            for index in pulled_sentences_by_groups[group]:
                row = {
                    'batch': self.batch.name,
                    'source': sentence,
                    'sentence': sentences[index].text,
                    'score': '{:.3f}'.format(scores[index]),
                    'similarity': group,
                    'sent_id': str(sentences[index].id)
                }
                result.append(row)

        if not result:
            return None

        result.sort(key=lambda entry: entry['score'], reverse=True)

        self.name = 'Report {} for {}'.format(
            self.batch.name,
            truncatechars(sentence, settings.SENTENCE_PREVIEW_LENGTH)
        )
        self.json = json.dumps(result)
        self.report_type = ReportTypes.SentSim.value
        self.save()

        alert = None
        if groups_sizes['medium'] or groups_sizes['low']:
            alert = 'Not enough sentences with '
            shortage = []
            if groups_sizes['medium']:
                shortage.append('score > 3')
            if groups_sizes['low']:
                shortage.append('score < 3')
            alert += ' or '.join(shortage)

        # There is no special DB field for this guy,
        # so just attach it as a usual object attribute
        if alert is not None:
            setattr(self, 'alert', alert)

        return self

    def get_csv_format(self):
        if self.report_type == ReportTypes.RegEx.value:
            return ['batch', 'regex', 'found', 'sentence']
        if self.report_type == ReportTypes.KeyWord.value:
            return ['batch', 'keywordlist', 'keyword', 'sentence']
        if self.report_type == ReportTypes.SentSim.value:
            return ['batch', 'source', 'sentence', 'score', 'similarity']
        return None

    def generate_csv(self):
        fieldnames = self.get_csv_format()
        if not self.json or fieldnames is None:
            return None
        filelike = StringIO()
        writer = csv.DictWriter(
            filelike, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC,
            extrasaction='ignore'
        )
        writer.writeheader()
        for row in json.loads(self.json):
            payload = {
                k: v for k, v in row.items()
            }
            writer.writerow(payload)
        return filelike

    def __str__(self):
        return self.name


class KeywordList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, unique=True)
    origin = models.CharField(max_length=4096)
    owner = models.ForeignKey(User, null=True, blank=True,
                              related_name='keywordlists', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    keyword_list = models.ForeignKey(KeywordList, related_name='keywords', null=True,on_delete=models.CASCADE)
    content = models.CharField(max_length=4096)

    def __str__(self):
        return self.content


@receiver(models.signals.post_save, sender=Keyword)
def keyword_cleanup(sender, instance, **kwargs):
    """ Drops unassigned keywords. """
    if not instance.keyword_list:
        instance.delete()
