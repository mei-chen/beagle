import time
import re
import uuid
import logging
import jsonfield
import collections
import datetime
import numpy as np

from collections import defaultdict
from copy import deepcopy
from itertools import ifilter
from unidecode import unidecode
from model_utils.models import TimeStampedModel
from notifications.models import Notification
from picklefield import PickledObjectField
from bulk_update.helper import bulk_update

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete
from django.contrib.contenttypes.models import ContentType

from ml.clfs import AGREEMENT_TYPE_CLASSIFIER
from nlplib import doclevel_process, sentlevel_process
from nlplib.utils import (
    linebreaks_to_markers,
    LINEBREAK_MARKER,
    preformat_markers
)
from core.signals import (
    external_invite_transformed, comment_posted, sentence_accepted, sentence_rejected,
    sentence_liked, sentence_unliked, sentence_disliked, sentence_undisliked,
    sentence_edited, sentence_undone, document_owner_changed, collaboration_invite_pre_delete
)
from core.exceptions import TooManyCommentsException
from dogbone.tools import lazydict
from utils.django_utils.model_utils import PendingModel, TrashableModel
from beagle_realtime.notifications import NotificationManager
from beagle_bot.tasks import ask_beagle
from integrations.s3 import get_s3_bucket_manager
from richtext.xmldiff import diff_change_sentence
from .tools import (
    user_to_dict, user_collaborators,
    batch_url, document_url, sentence_url,
    invalidate_user_cache
)

multispaces_re = re.compile('\s+', re.UNICODE)


class CollaboratorList(TimeStampedModel):
    user = models.OneToOneField(User, related_name='collaborator_aggregate')

    # A json formatted: {'suggestions': [{'email': user.email} for user in collaborators]}
    collaborator_suggestions = jsonfield.JSONField(null=True)

    @classmethod
    def create(cls, user):
        """
        Create a collaborator suggestion list for the user
        """
        l = CollaboratorList(user=user)
        l.save()

        return l

    @classmethod
    def add_suggestion(cls, user, email):
        try:
            suggestion_list = user.collaborator_aggregate
        except CollaboratorList.DoesNotExist:
            suggestion_list = CollaboratorList.create(user)

        suggestion_list.add_collaborator(email)

    def get_suggestions(self):
        """
        Return the list of email of the collaborators
        """
        if self.collaborator_suggestions is None:
            current_collaborators = user_collaborators(self.user)

            self.collaborator_suggestions = {
                'suggestions': [
                    {'email': u.email} for u in current_collaborators
                ]
            }

            self.save()

        return self.collaborator_suggestions['suggestions']

    def add_collaborator(self, email):
        """
        Add a new email to the list of suggestions
        """
        self.get_suggestions()

        if [s for s in self.collaborator_suggestions['suggestions'] if s['email'] == email]:
            return

        self.collaborator_suggestions['suggestions'].append({'email': email})
        self.save()

    def __unicode__(self):
        return unicode(self.user)


# Create a CollaboratorList each time a new User is created
@receiver(post_save, sender=User)
def create_collaborator_list(sender, **kwargs):
    if kwargs['created']:
        CollaboratorList.create(kwargs['instance'])


# Delete a CollaboratorList each time a User is deleted
@receiver(pre_delete, sender=User)
def delete_collaborator_list(sender, **kwargs):
    try:
        kwargs['instance'].collaborator_aggregate.delete()
    except CollaboratorList.DoesNotExist:
        pass


class NotTrashLightweightManager(models.Manager):
    """
    Get all objects that aren't deleted omitting the `cached_analysis` field
    - Makes the objects much more lightweight when loaded in memory
    """

    def get_query_set(self):
        return super(NotTrashLightweightManager, self).get_queryset() \
            .defer('cached_analysis') \
            .defer('sents') \
            .filter(trash=False)


class Batch(TimeStampedModel, TrashableModel, PendingModel):
    # The name of the batch
    name = models.CharField(max_length=200, null=False)

    # The list of document IDs that make up the batch
    docs = jsonfield.JSONField(null=True)  # IMPORTANT: use `documents` property instead

    # The user that uploaded the batch
    owner = models.ForeignKey(User)

    # The list of invalid document IDs that also were inside the batch
    # (temporary data used only once during the first processing immediately
    # after the uploading in order to send proper notifications to the user,
    # and cleaned up after that)
    invalid_docs = jsonfield.JSONField(null=True)

    class Meta:
        verbose_name_plural = 'batches'

    @property
    def documents_ids(self):
        """
        Exposes the list of documents (more precisely, their IDs) directly,
        because `docs` is an annoying dict of the following format:
            {'documents': [finally the useful list]}.
        """
        return self.docs['documents'] if self.docs else []

    documents_pks = documents_ids  # alias

    @property
    def documents_count(self):
        """ Returns the current number of unique documents in the batch. """
        return len(self.documents_pks)

    def get_documents_queryset(self):
        """ Returns a QuerySet of actual documents. """
        return Document.objects.filter(pk__in=self.documents_pks)

    def get_documents(self):
        """ Converts results from `get_documents_queryset` to a list. """
        return list(self.get_documents_queryset())

    def get_sorted_documents_queryset(self):
        """
        Does the same as `get_documents_queryset`, but also sorts the documents
        by their IDs, since the documents might have been added in any order.
        """
        return self.get_documents_queryset().order_by('id')

    def get_sorted_documents(self):
        """ Converts results from `get_sorted_documents_queryset` to a list. """
        return list(self.get_sorted_documents_queryset())

    def add_document(self, document):
        """
        Adds a document (passed either as an ID or as a Document instance)
        to the list of contained documents.
        """
        if not self.docs:
            self.docs = {'documents': []}

        document_id = document.id if isinstance(document, Document) else document

        if document_id not in self.docs['documents']:
            self.docs['documents'].append(document_id)
            self.save()
            return True

        return False

    def remove_document(self, document):
        """
        Removes a document (passed either as an ID or as a Document instance)
        from the list of contained documents.
        """
        if not self.docs:
            return False

        document_id = document.id if isinstance(document, Document) else document

        if document_id in self.docs['documents']:
            self.docs['documents'].remove(document_id)
            if not self.docs['documents']:
                self.docs = None
            self.save()
            return True

        return False

    @property
    def is_empty(self):
        """ Checks whether the batch is empty. """
        return self.documents_count == 0

    @property
    def is_trivial(self):
        """
        Checks whether the batch is empty or consists of only one document.
        """
        return self.documents_count <= 1

    @property
    def is_analyzed(self):
        """ Checks whether all the documents in the batch are processed. """
        # Make actual DB queries only in the pending state
        if self.is_pending:
            pending = self.get_documents_queryset().filter(
                pending=True
            ).exclude(
               pk__in=self.invalid_documents_pks
            ).exists()
            if not pending:
                self.pending = pending
                self.save()
        return self.is_ready

    def get_report_url(self):
        return batch_url(self)

    def get_batch_docstats(self, documents=None):
        if documents is None:
            documents = self.get_documents_queryset()

        batch_docstats = {
            'keywords': 0,
            'suggested': 0,
            'comments': 0,
            'redlines': 0,
        }

        for document in documents:
            docstats = document.get_docstats()

            batch_docstats['keywords'] += docstats['keywords']
            batch_docstats['suggested'] += docstats['suggested']
            batch_docstats['comments'] += docstats['comments']
            batch_docstats['redlines'] += docstats['redlines']

        return batch_docstats

    def to_dict(self, include_raw=False, include_analysis=False, include_docstats=False):
        analyzed = self.is_analyzed

        documents = self.get_documents_queryset()
        documents = documents.select_related('owner__details')
        documents = documents.order_by('-created')

        include_collaborators = self.is_trivial

        return {
            'batch_id': self.id,
            'analyzed': analyzed,
            'batch_name': self.name,
            'documents_count': self.documents_count,
            'owner': user_to_dict(self.owner),
            'created': str(self.created),
            'documents': [document.to_dict(include_raw=include_raw,
                                           include_analysis=include_analysis,
                                           include_docstats=include_docstats,
                                           include_collaborators=include_collaborators)
                          for document in documents],
            'report_url': self.get_report_url() if not self.is_trivial else '',
            'docstats': self.get_batch_docstats(documents) if analyzed and include_docstats else {},
        }

    def has_access(self, user):
        """ Checks whether `user` has access to the batch. """
        return user.is_superuser or self.owner == user

    def __unicode__(self):
        return self.name

    def delete(self, using=None):
        # Make sure to delete all the related notifications
        # before cascade deletion of the actual documents
        for document in self.get_documents_queryset():
            document.delete_notifications()
        super(Batch, self).delete(using=using)

    # Some duplicate utility methods for working with
    # `invalid_docs` the same way as with `docs`

    @property
    def invalid_documents_ids(self):
        return self.invalid_docs['documents'] if self.invalid_docs else []

    invalid_documents_pks = invalid_documents_ids  # alias

    @property
    def invalid_documents_count(self):
        return len(self.invalid_documents_pks)

    def get_invalid_documents(self):
        return list(Document.objects.filter(pk__in=self.invalid_documents_pks))

    def add_invalid_document(self, document):
        if not self.invalid_docs:
            self.invalid_docs = {'documents': []}

        document_id = document.id if isinstance(document, Document) else document

        if document_id not in self.invalid_docs['documents']:
            self.invalid_docs['documents'].append(document_id)
            self.save()
            return True

        return False

    def remove_invalid_document(self, document):
        if not self.invalid_docs:
            return False

        document_id = document.id if isinstance(document, Document) else document

        if document_id in self.invalid_docs['documents']:
            self.invalid_docs['documents'].remove(document_id)
            if not self.invalid_docs['documents']:
                self.invalid_docs = None
            self.save()
            return True

        return False


@receiver(post_save, sender=Batch)
def invalidate_batch_owner_cache_on_create(sender, **kwargs):
    if kwargs['created']:
        invalidate_user_cache(kwargs['instance'].owner)


@receiver(pre_delete, sender=Batch)
def invalidate_batch_owner_cache_on_delete(sender, **kwargs):
    invalidate_user_cache(kwargs['instance'].owner)


class Document(TimeStampedModel, TrashableModel, PendingModel):
    # How the document was originally named
    original_name = models.CharField('Original Name', max_length=300)

    # Human readable title
    title = models.CharField('Title', max_length=300)

    # uuid, suitable for embedding in urls
    uuid = models.CharField('UUID', max_length=100, unique=True)

    batch = models.ForeignKey(Batch, default=None, null=True, blank=True)

    # document category
    GENERIC = '-'
    NDA = 'NDA'
    AGREEMENT_TYPES = (
        (GENERIC, 'Agreement'),
        (NDA, 'NDA'),
    )

    DIGEST_CLAUSES = {
        GENERIC: collections.OrderedDict([
            ('LIABILITY', {'singular': 'Liability',
                           'plural': 'Liabilities'}),
            ('RESPONSIBILITY', {'singular': 'Responsibility',
                                'plural': 'Responsibilities'}),
            ('TERMINATION', {'singular': 'Termination',
                             'plural': 'Terminations'})
        ]),
        NDA: collections.OrderedDict([
            ('definition-on-confidential-information', {'singular': 'Confidential Information Definition',
                                                        'plural': 'Confidential Information Definitions'}),
            ('jurisdiction', {'singular': 'Jurisdiction Information',
                              'plural': 'Jurisdiction Information'}),
            ('return-destroy-information', {'singular': 'Return/Destroy Information',
                                            'plural': 'Return/Destroy Information'}),
            ('term-of-confidentiality', {'singular': 'Term of Confidentiality',
                                         'plural': 'Terms of Confidentiality'}),
            ('term-of-nda', {'singular': 'Term of NDA',
                             'plural': 'Terms of NDA'}),
            ('terminations', {'singular': 'Termination',
                              'plural': 'Terminations'})
        ])
    }

    agreement_type = models.CharField('Agreement Type', max_length=300, choices=AGREEMENT_TYPES, default=GENERIC,
                                      null=True)
    agreement_type_confidence = models.FloatField('Agreement Type Confidence', default=0., null=True)

    # Dirty flag
    dirty = models.BooleanField('Are annotations out of date?', default=False)

    # The state of Keywords at the time of doc's last analysis
    keywords_state = jsonfield.JSONField(null=True, default=None)
    # The state of Learners at the time of doc's last analysis
    learners_state = jsonfield.JSONField(null=True, default=None)

    # Doc-level extracted details, after NLP analysis
    doclevel_analysis = jsonfield.JSONField(load_kwargs={'object_pairs_hook': collections.OrderedDict}, null=True)

    cached_analysis = jsonfield.JSONField(load_kwargs={'object_pairs_hook': collections.OrderedDict}, null=True)

    # Saved copy of uploaded docx (if the case)
    docx_file = models.CharField('Docx Path', max_length=100, blank=True, null=True, default=None)

    # Saved copy of the uploaded docx into S3
    docx_s3 = models.CharField('S3 docx address', blank=True, null=True, max_length=255,
                               help_text='Format: bucket:filename')

    # Saved copy of the uploaded pdf into S3
    pdf_s3 = models.CharField('S3 pdf address', blank=True, null=True, max_length=255,
                              help_text='Format: bucket:filename')

    # Saved copy of the uploaded doc file into S3
    doc_s3 = models.CharField('S3 doc address', blank=True, null=True, max_length=255,
                              help_text='Format: bucket:filename')

    # the user that uploaded the document
    owner = models.ForeignKey(User)

    # List of sentence IDs that make up the document
    sents = jsonfield.JSONField(null=True)  # IMPORTANT: Use `model.sentences` property instead

    # Mark if prepared to export
    prepared = models.NullBooleanField('Prepared', default=False)

    # The used upload method
    upload_source = models.CharField('Upload Source', max_length=100, blank=True, null=True)

    # Is it an initial sample document?
    initsample = models.BooleanField('Is it an initial sample document?', default=False)

    # Processing timestamps
    processing_begin_timestamp = models.DateTimeField('Processing begin Timestamp', null=True, default=None)
    processing_end_timestamp = models.DateTimeField('Processing end Timestamp', null=True, default=None)

    # Time zone (used for proper handling of internal timestamps; calculated on uploading)
    time_zone = models.CharField('Time Zone', blank=True, null=True, max_length=50, default=None)

    ####################################
    # QUERY MANAGERS
    ####################################

    # Get objects excluding the `cached_analysis` field
    lightweight = NotTrashLightweightManager()

    @classmethod
    def analysis_workflow_start(cls, uploader, file_path, upload_source,
                                original_filename, title, batch,
                                send_notifications=True, time_zone=None):
        """
        :param uploader: the User model that uploads the document
        :param file_path: where the document is stored
        :param upload_source: from where the document was uploaded
        :param original_filename: the full file name
        :param title: the title of the document
        :param batch: the Batch model that contains the document
        :param send_notifications: if during the process we issue push notifications
        :param time_zone: the time zone in which internal timestamps should be considered
        :return:
        """
        from core.tasks import process_document_conversion

        document = Document(owner=uploader,
                            original_name=original_filename or '',
                            title=unidecode(title),
                            pending=True,
                            upload_source=upload_source,
                            batch=batch,
                            time_zone=time_zone)

        document.save()

        process_document_conversion.delay(document.pk, file_path, send_notifications)

        return document

    @classmethod
    def get_aggregated_documents(cls, user):
        """
        Get an aggregated list of documents, containing
        - documents owned by the user
        - documents the user has access to
        """

        is_owner = models.Q(owner=user)
        is_invited = models.Q(collaborationinvite__invitee=user)

        return Document.objects.filter(is_owner | is_invited).order_by('-created')

    @property
    def sentences_ids(self):
        """
        Exposes the list of sentences directly because sents is an annoying dict
        {'sentences': [finally the useful list]}
        """
        return (self.sents or {}).get('sentences', [])

    sentences_pks = sentences_ids  # alias

    @property
    def raw_text(self):
        """ Raw text generated from sentences' text """
        sents_text = []
        sents = self.get_sorted_sentences()
        for s in sents:
            sents_text.append(s.text)
        return ' '.join(sents_text)

    @property
    def analysis_result(self):
        """
        Compiles a dictionary for the whole analysis results of the document,
        both doc-level and sentence-level.
        If the `dirty` flag is set to True, a reanalysis is done.
        """
        if not self.sents:
            return None

        if self.dirty or not self.doclevel_analysis:
            self.analyse()
            self.cached_analysis = None
            self.dirty = False
            self.save()
        # `processed` is being saved in a cache
        elif self.cached_analysis:
            return self.cached_analysis

        processed = self.doclevel_analysis.copy()
        processed['sentences'] = []
        # Gather sentence-level from each sentence
        s_models = self.get_sorted_sentences()
        for idx, s_model in enumerate(s_models):
            s_dict = s_model.to_dict()
            s_dict['idx'] = idx
            # Fill in with sentence level only analysis results
            processed['sentences'].append(s_dict)

        # Add to cache - speeds-up the process
        self.cached_analysis = processed
        self.save()

        return processed

    @property
    def collaborators(self):
        return [ci.invitee for ci in self.collaborationinvite_set.all().select_related('invitee')]

    @staticmethod
    def preprocess_sentence(s):
        """
        Removes and counts trailing line-break markers.
        Also merges groups of adjacent whitespaces into single whitespaces.
        """
        sm = linebreaks_to_markers(s).strip()
        newlines = 0
        while sm.endswith(LINEBREAK_MARKER):
            newlines += 1
            sm = sm[:-len(LINEBREAK_MARKER)]
        return newlines, multispaces_re.sub(' ', sm).strip()

    def init(self, plaintext, formatted=None, styles=None, comments=None, changes=None):
        """
        Initializes the list of sentences from
          (plaintext_sentence_list, nodes_sentence_list, sentence_style_list,
           sentence_comments_list, sentence_change_list)
        """
        self.save()  # To acquire a pk that must be put into each sentence.doc
        self.dirty = True

        sentences = []

        if formatted is None:
            formatted = [None] * len(plaintext)
        if styles is None:
            styles = [None] * len(plaintext)
        if comments is None:
            comments = [None] * len(plaintext)
        if changes is None:
            changes = [None] * len(plaintext)

        edited_sentences = []
        for (s, f, style, s_comments, change) in zip(plaintext, formatted, styles, comments, changes):
            newlines, s_clnspace = self.preprocess_sentence(s)

            if s_comments:
                comment_dicts = []
                for comment in s_comments:
                    comment_dicts.append({
                        'uuid': str(uuid.uuid4()),
                        'message': comment[0],
                        'author': self.owner.username,
                        'timestamp': comment[1],
                        'is_imported': True,
                        'original_author': comment[2]
                    })
                imported_comments = {'comments': comment_dicts}
            else:
                imported_comments = None

            s_model = Sentence(
                text=s_clnspace,
                formatting=f,
                style=style,
                doc=self,
                deleted=False,
                accepted=True,
                rejected=False,
                modified_by=self.owner,
                newlines=newlines,
                comments=imported_comments,
            )
            s_model.save()

            sentences.append(s_model.pk)
            if change is not None:
                edited_sentences.append((s_model, change))

        self.sents = {'sentences': sentences}

        # Can edit appropriate sentences only after the document is fully
        # initialized with all its sentences
        for (s_model, change) in edited_sentences:
            newlines, s_clnspace = s_model.newlines, s_model.text
            newlines_changed, s_clnspace_changed = \
                self.preprocess_sentence(change)
            # If after preprocessing both revisions become equal,
            # then discard such changes as insignificant
            if newlines == newlines_changed and \
                    s_clnspace == s_clnspace_changed:
                continue
            if not s_clnspace_changed:
                self.delete_sentence(s_model, self.owner)
            else:
                s_model.edit(self.owner, s_clnspace_changed, None)

    def get_sentence_by_index(self, index):
        """
        Get the `Sentence` object belonging to the current document by index
        :param index:
        :return: the `Sentence` object or `None`
        """
        if not (0 <= index < len(self.sentences_pks)):
            return None

        try:
            return Sentence.objects.get(pk=self.sentences_pks[index])
        except Sentence.DoesNotExist:
            return None

    def doclevel_analyse(self):
        # Gather the text of all sentences
        sents = self.get_sorted_sentences()
        sents_text = [s.text for s in sents]

        d_analysis, _ = doclevel_process(sentences=sents_text)
        # Store the document level info
        self.doclevel_analysis = d_analysis

        # Detects the agreement type
        raw_text = ' '.join(sents_text)
        proba = AGREEMENT_TYPE_CLASSIFIER.predict_proba(raw_text)
        self.agreement_type = (Document.NDA
                               if np.argmax(proba) == 1
                               else Document.GENERIC)
        self.agreement_type_confidence = np.max(proba)

        self.save()

    def get_agreement_type(self):
        return None if self.agreement_type == Document.GENERIC else self.agreement_type

    def get_parties(self):
        """ Utility method for obtaining names of document's parties. """
        if not self.doclevel_analysis:
            self.doclevel_analyse()
        return {'you': self.doclevel_analysis['parties']['you']['name'],
                'them': self.doclevel_analysis['parties']['them']['name']}

    def get_parties_full(self):
        """ Utility method for obtaining full info on document's parties. """
        if not self.doclevel_analysis:
            self.doclevel_analyse()
        return self.doclevel_analysis['parties']

    def analyse(self):
        if not self.doclevel_analysis:
            self.doclevel_analyse()

        processed = self.doclevel_analysis.copy()

        # Gather the text of all sentences
        sents = self.get_sorted_sentences()
        sents_text = [s.text for s in sents]

        # Init a facade with the extracted parties
        ps = self.doclevel_analysis['parties']
        parties = (ps['them']['name'], ps['you']['name'],
                   (ps['them']['confidence'], ps['you']['confidence']))

        s_analysis, _ = sentlevel_process(sentences=sents_text, parties=parties, user=self.owner)

        # Add initial version for each sentence
        for i, s in enumerate(s_analysis['sentences']):
            # Init the annotations with the ones involving both parties
            annotations = [a for a in s.get('annotations', []) if a['party'] == 'both']
            # For the annotations involving a single party
            for annotation in [a for a in s.get('annotations', []) if a['party'] != 'both']:
                # If there isn't another identical annotation involving both parties
                if next(ifilter(lambda item: item['label'] == annotation['label'] and
                        item['sublabel'] == annotation['sublabel'], annotations), None) is None:
                    # Add the single party annotation to the sentence annotations
                    annotations.append(annotation)

            s_model = sents[i]

            s_model.extrefs = s.get('external_refs', None)

            # Add all annotations in tag form to the sentence
            if annotations:
                for ann in annotations:
                    s_model.add_tag(user=None,
                                    label=ann['label'],
                                    sublabel=ann['sublabel'],
                                    party=ann['party'],
                                    approved=True,
                                    annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)

        bulk_update(sents, batch_size=1000)

        return processed

    def invalidate_analysis(self):
        """
        Turns the `dirty` flag on, so that next time the analysis is requested,
        a reanalysis will be done.
        Use when sentence text was changed or when inconsistencies between the
        text and the annotations is caused.
        """
        self.dirty = True
        self.failed = False

    def invalidate_cache(self):
        """
        Although reanalysis is not required, the cache is inconsistent
        (sentences text has changed)
        """
        self.cached_analysis = None
        self.save()

    def update_sentence(self, old_sent, new_sent, reanalyze=False):
        """
        Replaces a sentence with a new version. Both `old_sent` and `new_sent`
        are Sentence objects.
        If `reanalyze` is set to True, a full reanalysis is being done.
        """
        for idx, spk in enumerate(self.sentences_pks):
            if spk == old_sent.pk:
                self.sentences_pks[idx] = new_sent.pk
        self.invalidate_cache()
        if reanalyze:
            self.analyse()
        self.save()

        return new_sent

    def delete_sentence(self, sentence, user):
        """
        Creates a new, deleted revision of the given sentence
        """
        deleted_sentence = sentence.delete(user)
        # There nothing to reanalyse since the sentence is dead
        deleted_sentence = self.update_sentence(sentence, deleted_sentence, reanalyze=False)
        self.save()

        return deleted_sentence

    def has_access(self, user):
        """
        Checks if `user` has access to the document (either as owner or as a collaborator)
        :param user:
        :return: boolean (if the user has access to the document)
        """
        return user.is_superuser or self.owner == user or user in self.collaborators

    def get_aggregated_collaborators(self):
        """ Returns a list of dicts with collaborators and external invites. """
        return (
            [ci.to_user_dict() for ci in self.collaborationinvite_set.all().select_related('invitee__details')] +
            [ei.to_user_dict() for ei in self.externalinvite_set.filter(pending=True)]
        )

    def get_report_url(self):
        return document_url(self)

    def get_docstats(self):
        analysis = self.analysis_result

        docstats = {
            'keywords': 0,
            'suggested': 0,
            'comments': 0,
            'redlines': 0,
        }

        if not analysis or 'sentences' not in analysis:
            return docstats

        for sn in analysis['sentences']:
            if not sn:
                continue

            if 'comments_count' in sn:
                docstats['comments'] += sn['comments_count']

            if not sn['accepted']:
                docstats['redlines'] += 1

            if sn['annotations']:
                # Count the learner annotations and keywords
                for an in sn['annotations']:
                    if an['type'] == 'K':
                        docstats['keywords'] += 1
                    elif an['type'] == 'S':
                        docstats['suggested'] += 1

        return docstats

    def to_dict(self, include_raw=False, include_analysis=True, include_docstats=False,
                include_collaborators=True):
        """
        Serialize a `Document` instance
        Params:
        * include_raw: bool: include or not the raw text extracted from the document
        * include_analysis: bool: include or not the processed text dictionary
        * include_docstats: bool: include or not the stats dictionary containing the number
                                  of changes, comments, different types of annotations
        * include_collaborators: bool: include the list of collaborators for the document
                                       (sometimes they are useless and can be safely omitted
                                       for the sake of better performance)
        Returns:
        * dict
        """
        d = {
            'status': int(self.is_ready),
            'failed': self.failed,
            'original_name': self.original_name,
            'title': self.title,
            'agreement_type': self.get_agreement_type(),
            'agreement_type_confidence': self.agreement_type_confidence,
            'uuid': self.uuid,
            'document_id': self.id,
            'owner': user_to_dict(self.owner),
            'collaborators': self.get_aggregated_collaborators() if include_collaborators else None,
            'created': str(self.created),
            'is_initsample': self.initsample,
            'processing_begin_timestamp': self.processing_begin_timestamp.isoformat() if self.processing_begin_timestamp else None,
            'processing_end_timestamp': self.processing_end_timestamp.isoformat() if self.processing_end_timestamp else None,
            'url': reverse('document_detail_view', kwargs={'uuid': self.uuid}),
            'report_url': self.get_report_url(),
        }

        if self.keywords_state:
            d['keywords_state'] = self.keywords_state
        if self.learners_state:
            d['learners_state'] = self.learners_state

        if self.failed:
            d['error_message'] = self.error_message

        if self.is_pending:
            return d

        if include_raw:
            d['text'] = self.raw_text

        if include_analysis:
            d['analysis'] = self.analysis_result
        else:
            d['analysis'] = self.doclevel_analysis

        if include_docstats:
            d['docstats'] = self.get_docstats()

        return d

    def digest(self):
        if not self.is_ready:
            return None

        agreement_type = self.agreement_type
        if agreement_type is None or agreement_type not in Document.DIGEST_CLAUSES:
            agreement_type = Document.GENERIC

        # Init the digest
        digest_dict = {'annotations': [], 'keywords': []}

        # Add parties to digest
        digest_dict['parties'] = self.get_parties()

        label_stats_sort_key = lambda item: (-item['total'], item['label'])

        ################################################################################
        #
        #   Grammar annotations
        #
        ################################################################################

        # Init the annotations
        annotations_dict = lazydict(generator=lambda label: {
            'total': 0,
            'by_party': {'none': 0, 'you': 0, 'them': 0},
            'display_plural': Document.DIGEST_CLAUSES[agreement_type][label]['plural'],
            'display_singular': Document.DIGEST_CLAUSES[agreement_type][label]['singular'],
            'clauses': [],
            'label': label
        })

        for sentence in self.analysis_result['sentences']:
            annotations = sentence.get('annotations')
            if not annotations:
                continue

            for annotation in annotations:
                label = annotation.get('label')

                if not label or label not in Document.DIGEST_CLAUSES[agreement_type]:
                    continue

                annotations_dict[label]['total'] += 1

                if annotation['party'] not in ('them', 'you'):
                    annotations_dict[label]['by_party']['none'] += 1
                else:
                    annotations_dict[label]['by_party'][annotation['party']] += 1

                clause = preformat_markers(sentence['form'])
                annotations_dict[label]['clauses'].append(clause)

        for annotation_name in Document.DIGEST_CLAUSES[agreement_type]:
            digest_dict['annotations'].append(annotations_dict[annotation_name])

        ################################################################################
        #
        #   Keywords
        #
        ################################################################################

        keywords_dict = lazydict(generator=lambda label: {
            'total': 0,
            'clauses': [],
            'label': label
        })

        for sentence in self.analysis_result['sentences']:
            annotations = sentence.get('annotations')
            if not annotations:
                continue

            for annotation in annotations:
                if annotation.get('type') != SentenceAnnotations.KEYWORD_TAG_TYPE:
                    continue

                label = annotation.get('label')

                if not label:
                    continue

                keywords_dict[label]['total'] += 1

                clause = re.sub(r'(%s)' % label, r'<b>\1</b>',
                                preformat_markers(sentence['form']),
                                flags=re.IGNORECASE)
                keywords_dict[label]['clauses'].append(clause)

        digest_dict['keywords'] = sorted(keywords_dict.values(),
                                         key=label_stats_sort_key)

        ################################################################################
        #
        #   Online learners & Spot experiments
        #
        ################################################################################

        learners_dict = lazydict(generator=lambda classifier_id: {
            'total': 0,
            'label': None,
            'clauses': [],
            'classifier_id': classifier_id
        })

        experiments_dict = lazydict(generator=lambda experiment_uuid: {
            'total': 0,
            'label': None,
            'clauses': [],
            'experiment_uuid': experiment_uuid
        })

        for sentence in self.analysis_result['sentences']:
            annotations = sentence.get('annotations')
            if not annotations:
                continue

            for annotation in annotations:
                if annotation.get('type') != SentenceAnnotations.SUGGESTED_TAG_TYPE:
                    continue

                label = annotation.get('label')

                if not label:
                    continue

                classifier_id = annotation.get('classifier_id')
                if classifier_id:
                    learners_dict[classifier_id]['total'] += 1
                    learners_dict[classifier_id]['label'] = label

                    clause = preformat_markers(sentence['form'])
                    learners_dict[classifier_id]['clauses'].append(clause)

                experiment_uuid = annotation.get('experiment_uuid')
                if experiment_uuid:
                    experiments_dict[experiment_uuid]['total'] += 1
                    label = label.replace('[Spot] ', '')
                    experiments_dict[experiment_uuid]['label'] = label

                    clause = preformat_markers(sentence['form'])
                    experiments_dict[experiment_uuid]['clauses'].append(clause)

        digest_dict['learners'] = sorted(learners_dict.values(),
                                         key=label_stats_sort_key)

        digest_dict['experiments'] = sorted(experiments_dict.values(),
                                            key=label_stats_sort_key)

        return digest_dict

    def save(self, *args, **kwargs):
        """ Auto generate an url friendly unique ID """
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        is_new = self.id is None
        super(Document, self).save(*args, **kwargs)
        if is_new:
            # Add the document to batch only once after the first save
            self.add_to_batch()

    def delete(self, using=None):
        self.delete_notifications()
        self.trash = True
        self.collaborationinvite_set.all().delete()
        self.externalinvite_set.all().delete()
        self.save()
        self.remove_from_batch()

    def delete_instance(self):
        self.delete_notifications()
        super(Document, self).delete()

    def delete_notifications(self):
        document_ct = ContentType.objects.get_for_model(self).pk
        Notification.objects.filter(Q(action_object_object_id=self.pk,
                                      action_object_content_type=document_ct) |
                                    Q(target_object_id=self.pk,
                                      target_content_type=document_ct)).delete()

    def change_owner(self, new_owner):
        """
        Change the owner of the document
        :param new_owner:
        :return: the old owner
        """

        # Change the owner and save the model
        old_owner = self.owner
        self.owner = new_owner
        self.save()

        # Send the `core.signals.document_owner_changed` signal
        document_owner_changed.send(sender=self.__class__, document=self, before_owner=old_owner, after_owner=new_owner)

        return old_owner

    def save_docx(self, file_handle):
        """
        Save a docx file to S3 and update the `docx_s3` field on the model
        :param file_handle: The docx file handle we want saved and associated with this document
        :return: None
        """
        s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
        file_name = '%s.docx' % str(uuid.uuid4())
        s3_file_path = 'uploads/media/%s' % file_name
        s3_bucket.save_file(s3_file_path, file_handle)
        self.docx_s3 = '%s:%s' % (settings.UPLOADED_DOCUMENTS_BUCKET, s3_file_path)
        self.save()

    def get_docx(self):
        """
        Get the docx file from S3
        :return: file like object
        """

        if self.docx_s3 is None:
            return None

        s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
        s3_key = self.docx_s3.split(':')[1]
        return s3_bucket.read_to_file(s3_key)

    def save_pdf(self, file_handle):
        """
        Save a pdf file to S3 and update the `pdf_s3` field on the model
        :param file_handle: The pdf file handle we want saved and associated with this document
        :return: None
        """
        s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
        file_name = '%s.pdf' % str(uuid.uuid4())
        s3_file_path = 'uploads/media/%s' % file_name
        s3_bucket.save_file(s3_file_path, file_handle)
        self.pdf_s3 = '%s:%s' % (settings.UPLOADED_DOCUMENTS_BUCKET, s3_file_path)
        self.save()

    def save_doc(self, file_handle):
        """
        Save a doc file to S3 and update the `doc_s3` field on the model
        :param file_handle: The doc file handle we want saved and associated with this document
        :return: None
        """
        s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
        file_name = '%s.doc' % str(uuid.uuid4())
        s3_file_path = 'uploads/media/%s' % file_name
        s3_bucket.save_file(s3_file_path, file_handle)
        self.doc_s3 = '%s:%s' % (settings.UPLOADED_DOCUMENTS_BUCKET, s3_file_path)
        self.save()

    def get_pdf(self):
        """
        Get the pdf file from S3
        :return: file like object
        """

        if self.pdf_s3 is None:
            return None

        s3_bucket = get_s3_bucket_manager(bucket_name=settings.UPLOADED_DOCUMENTS_BUCKET)
        s3_key = self.pdf_s3.split(':')[1]
        return s3_bucket.read_to_file(s3_key)

    def get_sentences_queryset(self):
        return Sentence.objects.filter(pk__in=self.sentences_pks)

    def get_sentences(self):
        return list(self.get_sentences_queryset())

    def get_sorted_sentences(self):
        sentences = self.get_sentences()
        indexed_pks = {spk: idx for idx, spk in enumerate(self.sentences_pks)}
        sentences.sort(key=lambda s: indexed_pks[s.pk])
        return sentences

    def add_to_batch(self):
        """ Adds the document to the containing batch. """
        if self.batch:
            self.batch.add_document(self)

    def remove_from_batch(self):
        """ Removes the document from the containing batch. """
        if self.batch:
            self.batch.remove_document(self)
            self.batch = None
            self.save()

    def get_user_view_dates(self):
        """ Returns a dict { int:user_pk: datetime:last_view_date } """

        viewdate_set = self.userlastviewdate_set.all()
        result = {}

        for viewdate in viewdate_set:
            result[viewdate.user.pk] = viewdate.date

        return result

    def get_user_view_dates_str(self):
        """ Returns a dict { str:username: str:last_view_date } """

        viewdate_set = self.userlastviewdate_set.all()
        result = {}

        for viewdate in viewdate_set:
            username = viewdate.user.get_username()
            date = viewdate.date.astimezone(timezone.get_current_timezone())
            result[username] = date.strftime("%Y-%m-%d %H:%M")

        return result

    def __unicode__(self):
        return self.title


@receiver(post_save, sender=Document)
def update_parent_batch_pending_flag(sender, **kwargs):
    document = kwargs['instance']
    if document.is_pending:
        batch = document.batch
        if batch and batch.is_ready:
            batch.pending = True
            batch.save()


class UserLastViewDate(models.Model):
    """
    Represents last user view of specific document.

    Created when user views document for the first time.
    Updates when document is viewed by same user again.
    """

    document = models.ForeignKey(Document)
    user = models.ForeignKey(User)
    date = models.DateTimeField()

    @staticmethod
    def create_or_update(document, user, date):
        try:
            viewdate = UserLastViewDate.objects.get(
                document=document,
                user=user
            )
            viewdate.date = date
            viewdate.save()

        except UserLastViewDate.DoesNotExist:
            UserLastViewDate.objects.create(
                document=document,
                user=user,
                date=date
            )


class SentenceLock(TimeStampedModel):
    # Owner of this lock
    owner = models.ForeignKey(User, null=True, default=None)
    # Life time of this lock (minutes until expiry)
    lifetime = models.IntegerField(default=60)

    # Time created is handled by TimeStampedModel

    @property
    def expiry_time(self):
        lifetime = timezone.timedelta(minutes=self.lifetime)
        return self.created + lifetime

    @property
    def is_expired(self):
        # return `now` is past `expiry_time`
        return timezone.now() >= self.expiry_time

    def to_dict(self):
        return {
            'sentence': self.sentence.uuid,
            'docUUID': self.sentence.doc.uuid,
            'owner': user_to_dict(self.owner),
            'expiry_time': str(self.expiry_time)
        }

    def __unicode__(self):
        return "Lock [%s] %s" % (str(self.owner), str(self.is_expired))

    class SentenceLockException(Exception):
        pass


class CommentType:
    """
    Enum for types of comments

    `STANDARD` - Standard user interaction on a sentence thread
        ACTIONS:
            1) Save the comment
            2) Send realtime notifications
    `BEAGLEBOT_REQUEST` - The user is requesting @beagle's assistance
        ACTIONS:
            1) Pass the comment to Luis.ai
            2) Check that the requirements are met
            3) Search on wikipedia for the requested resources
            4) Send realtime notifications

    """
    STANDARD = 0
    BEAGLEBOT_REQUEST = 1

    class DefaultMentions:
        BEAGLEBOT = frozenset(['beaglebot', 'beagle', 'beagleai'])

    MENTION_PATTERN = re.compile(r"@\[([a-zA-Z0-9\-_\.@]+)\]")

    @classmethod
    def extract_mentions(cls, comment):
        return cls.MENTION_PATTERN.findall(comment)

    @classmethod
    def detect(cls, mentions):
        lower_mentions = set(m.lower() for m in mentions)

        # TODO: maybe make this a bit more elaborate in the future
        if lower_mentions.intersection(cls.DefaultMentions.BEAGLEBOT):
            return cls.BEAGLEBOT_REQUEST

        return cls.STANDARD


class SentenceAnnotations:
    MANUAL_TAG_TYPE = 'M'  # Tags added by the user
    SUGGESTED_TAG_TYPE = 'S'  # Tags auto-added by the Learners (based on manual tags)
    ANNOTATION_TAG_TYPE = 'A'  # Grammar based tags (Main subset: RLT)
    KEYWORD_TAG_TYPE = 'K'  # Keyword based tags (sentence matches keyword)


class Sentence(TimeStampedModel):
    # UUID common for all the versions of the same sentence
    uuid = models.CharField('UUID', max_length=100, db_index=True)
    # Text content
    text = models.TextField('Sentence text')
    # Formatting flags
    formatting = jsonfield.JSONField('Formatted contents', null=True, blank=True)
    # Formatting flags
    style = jsonfield.JSONField('Style attributes', null=True, blank=True)
    # Delete flag
    deleted = models.BooleanField('Is it deleted?', default=False)
    # Accepted flag
    accepted = models.BooleanField('Is it accepted?', default=False)
    # Rejected flag
    rejected = models.BooleanField('Is it rejected?', default=False)
    # Edit lock
    lock = models.OneToOneField(SentenceLock, null=True, blank=True)
    # Comments thread
    comments = jsonfield.JSONField('List of comments', null=True, blank=True)
    # Ext Refs
    extrefs = jsonfield.JSONField('List of external references', null=True, blank=True)
    # Parent document
    doc = models.ForeignKey(Document)
    # User that created this version
    modified_by = models.ForeignKey(User)
    # List of users that liked/disliked it
    likes = jsonfield.JSONField('Likes', null=True, blank=True)
    # Number of trailing line-breaks
    newlines = models.IntegerField('Trailing line-breaks', default=0)

    # Where tags of all shapes and colors united
    annotations = jsonfield.JSONField('Annotations', null=True, blank=True, default=None)

    # History navigation
    prev_revision = models.OneToOneField('Sentence', null=True, blank=True, related_name='next_revision')

    def get_report_url(self, sentence_index):
        return sentence_url(self, sentence_index)

    @classmethod
    def expand_comment_dict(cls, comment, sentence, document):
        # There is a weird mutation bug with the comments: when the loop runs
        # again it replaces the author with the result of user_to_dict
        _comment = deepcopy(comment)
        try:
            if comment['author'] == '@beagle':
                _comment['author'] = {'username': '@beagle'}
            else:
                _comment['author'] = user_to_dict(User.objects.get(username=comment['author']))
            return _comment
        except (User.DoesNotExist, KeyError):
            return None

    @property
    def latest_approved_revision(self):
        all_revisions = Sentence.objects.filter(uuid=self.uuid)
        accepted_revs = all_revisions.filter(accepted=True)
        try:
            latest = accepted_revs.order_by('-id')[0]
        except IndexError:  # this should not occur in normal circumstances
            latest = None
        return latest

    @property
    def latest_revision(self):
        all_revisions = Sentence.objects.filter(uuid=self.uuid)
        try:
            latest = all_revisions.order_by('-id')[0]
        except IndexError:  # this should not occur in normal circumstances
            latest = None
        return latest

    def find_index(self):
        """
        Find the index of the sentence inside the document
        """
        latest = self.latest_revision
        try:
            return self.doc.sentences_pks.index(latest.pk)
        except IndexError:
            return None

    @property
    def first_revision(self):
        curr_rev = self
        while curr_rev.prev_revision:
            curr_rev = curr_rev.prev_revision
        return curr_rev

    def save(self, *args, **kwargs):
        """ Auto generate an url friendly unique ID """
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(Sentence, self).save(*args, **kwargs)

    def _likes_export(self):
        """ Turn user pks into usernames in the like/dislike lists """
        if not self.likes:
            return None

        likes = []
        dislikes = []
        for upk in self.likes['likes']:
            try:
                u = User.objects.get(pk=upk)
                likes.append(user_to_dict(u))
            except User.DoesNotExist:
                logging.warning('User that liked something doesn\'t exist anymore.')
                pass

        for upk in self.likes['dislikes']:
            try:
                u = User.objects.get(pk=upk)
                dislikes.append(user_to_dict(u))
            except User.DoesNotExist:
                logging.warning('User that disliked something doesn\'t exist anymore.')
                pass

        return {'likes': likes, 'dislikes': dislikes}

    def to_dict(self, get_latest=True, get_recent_comments=True, get_total_comments_count=True):
        s = {'form': self.text,
             'style': self.style,
             'uuid': self.uuid,
             'doc': self.doc.uuid,
             'external_refs': self.extrefs,
             'accepted': self.accepted,
             'rejected': self.rejected,
             'deleted': self.deleted,
             'modified_by': self.modified_by.username,
             'likes': self._likes_export(),
             'lock': self.lock.to_dict() if self.is_locked else None,
             'newlines': self.newlines,
             'annotations': self.annotations['annotations'] if self.annotations else None
             }

        if get_recent_comments:
            s['comments'] = self.recent_comments

        if get_total_comments_count:
            if not self.comments or 'comments' not in self.comments:
                s['comments_count'] = 0
            else:
                s['comments_count'] = len(self.comments['comments'])

        if get_latest and not self.accepted:
            latest = self.latest_approved_revision
            if latest:
                s['latestRevision'] = latest.to_dict(get_latest=False)

        if LINEBREAK_MARKER in self.text:
            s['contains_linebreaks'] = True
        return s

    def clone(self):
        """
        Makes a clone of the current sentence.
        For making new revisions, use `new_revision`, or one of the methods:
            `delete`, `accept`, `reject`
        """
        return Sentence(text=self.text,
                        deleted=self.deleted,
                        accepted=self.accepted,
                        rejected=self.rejected,
                        style=deepcopy(self.style),
                        annotations=deepcopy(self.annotations),
                        extrefs=deepcopy(self.extrefs),
                        formatting=deepcopy(self.formatting),
                        doc=self.doc,
                        comments=self.comments,
                        lock=None,
                        newlines=self.newlines,
                        uuid=self.uuid,
                        modified_by=self.modified_by)

    # TODO: Add extrefs modification support
    def new_revision(self, user, text=None, annotations=None, reanalyze=False):
        """
        Returns a new revision. Takes care of saving, history links and
        reanalysis if reanalyze is True
        """

        # Clone the old revision
        s = self.clone()

        # Change fields
        s.modified_by = user
        s.accepted = False
        s.rejected = False
        s.prev_revision = self

        # Persist the sentence so that we have a PK
        s.save()

        # Get the lock from the old sentence
        available_lock = self.lock

        # Set the lock on the old sentence to None
        self.lock = None
        self.save()

        # Put the lock on the new sentence
        s.lock = available_lock

        # Apply the edits
        if text is not None:
            # No new revision if no changes (#140)
            if s.text == text:
                return self
            if s.formatting is not None:
                # Make the old formatting correspond to the new text
                s.formatting = diff_change_sentence(s.text, text, s.formatting)
            s.text = text
        if annotations is not None:
            s.annotations = annotations
        elif reanalyze and s.annotations is not None:
            # The system annotations will be regenerated, so discard the old
            s.annotations = [a for a in s.annotations['annotations']
                             if 'type' not in a or a['type'] != SentenceAnnotations.ANNOTATION_TAG_TYPE]

        s.save()

        if reanalyze:
            self.doc.update_sentence(self, s)
            self.doc.analyse()
            s = Sentence.objects.get(pk=s.pk)  # The object is not synched to model
            self.doc.save()

        return s

    def delete(self, user):
        """ Returns a new revision by applying a delete operation """

        # TODO: Don't override the predefined model methods
        # Create another method, named differently

        s = self.new_revision(user)
        s.deleted = True

        s.save()
        return s

    def delete_instance(self):
        super(Sentence, self).delete()

    def accept(self, user):
        """ Returns a new revision by applying an accept operation """
        s = self.new_revision(user)
        s.accepted = True

        s.save()
        sentence_accepted.send(sender=self.__class__, sentence=self)
        return s

    def reject(self, user):
        """ Returns a new revision by applying a reject operation """
        # Mark as rejected
        self.rejected = True
        self.save()

        # Get the newest unrejected
        s_fallback = self.prev_revision
        if s_fallback is None:
            # this shouldn't happen, but just in case
            logging.error("Sentence.reject: trying to reject a sentence that "
                          "doesn't have a previous version - %s" % self.pk)
            return self
        while s_fallback.rejected and s_fallback.prev_revision:
            s_fallback = s_fallback.prev_revision

        # Make a new reverted revision
        s_revert = s_fallback.clone()
        s_revert.modified_by = user
        # Mark fallback as rejected so it's never considered for revert again
        s_fallback.rejected = True
        s_fallback.save()
        # History
        s_revert.prev_revision = self
        # Port back the annotations (just in case)
        s_revert.annotations = self.annotations
        # Port back comments
        s_revert.comments = self.comments
        s_revert.save()

        # Reverts to the latest approved version
        # By putting a clone of that on top of the rejected version
        sentence_rejected.send(sender=self.__class__, sentence=self)
        return s_revert

    def undo(self, user):
        """ Returns a new revision after applying an undo operation """
        # Get the the previous revision
        s_prev = self.prev_revision
        if s_prev is None:
            # this shouldn't happen, but just in case
            logging.error("Sentence.undo: trying to undo a sentence that "
                          "doesn't have a previous version - %s" % self.pk)
            return self

        # Make a new undone revision
        s_revert = s_prev.clone()
        s_revert.modified_by = user
        # History
        s_revert.prev_revision = self
        s_revert.save()

        # Undoes to the previous version
        # By putting a clone of that on top of the current version
        sentence_undone.send(sender=self.__class__, sentence=self)
        return s_revert

    def like(self, user):
        """ Marks the current revision as liked (adds :user to the list) """
        if not self.likes:
            self.likes = {'likes': [user.pk], 'dislikes': []}
        else:
            if user.pk not in self.likes['likes']:
                self.likes['likes'].append(user.pk)
            # Toggle effect
            if user.pk in self.likes['dislikes']:
                self.likes['dislikes'].remove(user.pk)
        self.save()
        sentence_liked.send(sender=self.__class__, sentence=self, user=user)
        return self

    def remove_like(self, user):
        """ Clears :user from the likes list """
        if not self.likes:
            return False
        else:
            if user.pk in self.likes['likes']:
                self.likes['likes'].remove(user.pk)
            else:
                return False
        self.save()
        sentence_unliked.send(sender=self.__class__, sentence=self, user=user)
        return self

    def dislike(self, user):
        """ Marks the current revision as disliked (adds :user to the list) """
        if not self.likes:
            self.likes = {'dislikes': [user.pk], 'likes': []}
        else:
            if user.pk not in self.likes['dislikes']:
                self.likes['dislikes'].append(user.pk)
            # Toggle effect
            if user.pk in self.likes['likes']:
                self.likes['likes'].remove(user.pk)
        self.save()
        sentence_disliked.send(sender=self.__class__, sentence=self, user=user)
        return self

    def remove_dislike(self, user):
        """ Clears :user from the dislikes list """
        if not self.likes:
            return False
        else:
            if user.pk in self.likes['dislikes']:
                self.likes['dislikes'].remove(user.pk)
            else:
                return False
        self.save()
        sentence_undisliked.send(sender=self.__class__, sentence=self, user=user)
        return self

    def add_tag(self, user, label, sublabel=None, party=None, approved=False,
                annotation_type=SentenceAnnotations.MANUAL_TAG_TYPE,
                classifier_id=None, experiment_uuid=None):
        """
        Returns True if successfully added, False if it's a duplicate
        Note: duplicates are allowed for ANNOTATION_TAG_TYPE
        """
        if not label:
            return False

        annotation = {
            'type': annotation_type,
            'label': label,
            'sublabel': sublabel,
            'user': user.username if user is not None else None,
            'party': party,
            'approved': approved,
            'classifier_id': classifier_id,
            'experiment_uuid': experiment_uuid,
        }

        if not self.annotations or 'annotations' not in self.annotations:
            self.annotations = {'annotations': [annotation]}
            self.doc.invalidate_cache()
            self.save()
            return True

        # For ANNOTATION type allow duplicates, for the others don't
        if annotation_type != SentenceAnnotations.ANNOTATION_TAG_TYPE:
            # Look if the annotation already exists
            for ann in self.annotations['annotations']:
                if sublabel is None and ann['label'] == label:
                    return False

        self.annotations['annotations'].append(annotation)
        self.doc.invalidate_cache()
        self.save()
        return True

    def get_tags(self, excluded=[]):
        """
        Utility method for obtaining unique sentence's tags
        (i.e. annotations' labels).
        Parameter :excluded can be used for filtering tags by type
        (by default all types of tags are fetched).
        """
        tags = []
        if self.annotations and 'annotations' in self.annotations:
            tags = [ann['label'] for ann in self.annotations['annotations']
                    if ann['type'] not in excluded]
        return sorted(set(tags))

    def get_tags_by_type(self, excluded=[]):
        tags_by_type = defaultdict(set)
        if self.annotations and 'annotations' in self.annotations:
            for ann in self.annotations['annotations']:
                if ann['type'] not in excluded:
                    tags_by_type[ann['type']].add(ann['label'])
        return tags_by_type

    def remove_tag(self, user, label, sublabel=None, party=None):
        """ Returns the actual annotation if successfully removed, None otherwise """
        if not self.annotations or 'annotations' not in self.annotations:
            return False

        for i, ann in enumerate(self.annotations['annotations']):
            # Ensure the tag is in fact attributed to the sentence
            if ann['label'] == label:
                # # If this is an 'annotation' duplicates are possible
                # # only check ANNOTATION_TAG_TYPES for matches on other attributes
                # if ann['type'] == ANNOTATION_TAG_TYPE:
                #     # If the other attributes match, this is indeed the tag to delete
                #     if ann['sublabel'] == sublabel and ann['party'] == party:
                #         # nuke it whole
                #         self.annotations['annotations'].pop(i)
                #         break
                #     else:
                #         continue
                # If this is party specific and different, skip (OOLIE: might apply with different online learners later???)
                # if ann['party'] != party:
                #    continue
                # Else, nuke it whole
                annotation = self.annotations['annotations'].pop(i)
                break
        else:
            # Tag not found
            return

        self.doc.invalidate_cache()
        self.save()
        return annotation

    @property
    def recent_comments(self):
        """ Returns the first page of comments. Uses settings.COMMENTS_PER_PAGE """
        if self.comments is not None:
            return [Sentence.expand_comment_dict(comment, self, self.doc)
                    for comment in self.comments['comments'][:settings.COMMENTS_PER_PAGE]]
        return None

    def add_comment(self, user, comment, timestamp=None, is_imported=False):
        if len(comment) > 1500:
            comment = '%s...' % comment[:1500]
        current_comments = self.comments
        if current_comments and len(current_comments['comments']) > 999:
            raise TooManyCommentsException()
        if not timestamp:
            timestamp = time.time()
        comment_dict = {
            'uuid': str(uuid.uuid4()),
            'message': comment,
            'author': user.username,
            'timestamp': timestamp,
        }
        if is_imported:
            comment_dict['is_imported'] = is_imported

        if not self.comments or 'comments' not in self.comments:
            self.comments = {'comments': [comment_dict]}
        else:
            self.comments['comments'].insert(0, comment_dict)

        self.doc.invalidate_cache()
        self.save()

        comment_posted.send(sender=self.__class__, sentence=self, author=user, comment=comment)
        return comment_dict

    def get_comments(self, include_imported=True):
        comments = (self.comments or {}).get('comments', [])
        if not include_imported:
            comments = [comment for comment in comments
                        if not comment.get('is_imported')]
        return comments

    def edit(self, author, text, annotations, reanalyze=False):
        new_sentence = self.new_revision(
            author,
            text=text,
            annotations=annotations,
            reanalyze=reanalyze)

        self.doc.update_sentence(self, new_sentence)
        self.doc.save()

        sentence_edited.send(sender=self.__class__, sentence=self, author=author)

        return new_sentence

    def add_beaglebot_comment(self, response, response_type):
        comment_dict = {
            'uuid': str(uuid.uuid4()),
            'message': None,
            'author': '@beagle',
            'response_type': response_type,  # Wikipedia, DefinitionTool, etc ...
            'response': response,
            'timestamp': time.time(),
        }
        if not self.comments or 'comments' not in self.comments:
            self.comments = {'comments': [comment_dict]}
        else:
            self.comments['comments'].insert(0, comment_dict)
        self.doc.invalidate_cache()
        self.save()

        return comment_dict

    def remove_comment(self, user, comment_uuid):
        """ Returns True if successfully removed, False otherwise """
        if not self.comments or 'comments' not in self.comments:
            return False
        try:
            for i, comm in enumerate(self.comments['comments']):
                if comm['uuid'] == comment_uuid:
                    # Remove the comment
                    self.comments['comments'].pop(i)
                    break
            self.doc.invalidate_cache()
            self.save()
            return True
        except ValueError:
            logging.error("Encountered Error in remove_comment comment_uuid=%s", comment_uuid)
            return False

    ### Lock methods

    @property
    def is_locked(self):
        if self.lock is None:
            return False
        if self.lock.is_expired:
            self.lock = None
            self.save()
            return False
        else:
            return True

    @property
    def lock_owner(self):
        if self.lock is None:
            return None
        else:
            return self.lock.owner

    def acquire_lock(self, lock_owner, lifetime=60):
        if self.lock is not None:
            msg = "Cannot acquire lock on sentence, one already exists"
            raise SentenceLock.SentenceLockException(msg)
        lock = SentenceLock(owner=lock_owner, lifetime=lifetime)
        lock.save()
        self.lock = lock
        self.save()
        return True

    def release_lock(self):
        if self.lock is None:
            msg = "Tried to release a lock where none was held"
            raise SentenceLock.SentenceLockException(msg)
        self.lock = None
        self.save()
        return True

    ### Magic methods

    def __unicode__(self):
        """
        We don't need the actual text representation of the sentence for the admin
        - We will use the unicode of the document because it helps us with notification display
        """
        return unicode(self.doc)


class CollaborationInvite(TimeStampedModel):
    # The person that invites
    inviter = models.ForeignKey(User, related_name='invitations_sent')

    # The person that is invited
    invitee = models.ForeignKey(User, related_name='invitations_received')

    # The document that the person is invited to
    document = models.ForeignKey(Document)

    # The invite might have a sentence attached (which we don't even expose through API),
    # used just to redirect the invited user to the right place
    sentence = models.ForeignKey(Sentence, null=True)

    def to_dict(self):
        return {
            'inviter': user_to_dict(self.inviter),
            'invitee': user_to_dict(self.invitee),
            'document': self.document.to_dict(include_analysis=False,
                                              include_docstats=True),
            'external': False,
            'id': self.id
        }

    def to_user_dict(self):
        return user_to_dict(self.invitee)

    def __unicode__(self):
        return u"From: '%s' To: '%s' On: '%s'" % (
            self.inviter.email,
            self.invitee.email,
            unicode(self.document),
        )


@receiver(post_save, sender=CollaborationInvite)
def invalidate_collaboration_invite_invitee_cache_on_create(sender, **kwargs):
    if kwargs['created']:
        invalidate_user_cache(kwargs['instance'].invitee)


@receiver(pre_delete, sender=CollaborationInvite)
def invalidate_collaboration_invite_invitee_cache_on_delete(sender, **kwargs):
    invalidate_user_cache(kwargs['instance'].invitee)


class ExternalInvite(TimeStampedModel, PendingModel):
    """
    When a user invites an email that is not registered with Beagle
    we create an external invite and send emails
    """

    # The invite email
    email = models.EmailField()

    # The document the user is invited to
    document = models.ForeignKey(Document, null=True, default=None)

    # The specific sentence the user might be invited to
    sentence = models.ForeignKey(Sentence, null=True, default=None)

    # The user that issued the invite
    inviter = models.ForeignKey(User)

    # The timestamp when the invite email was sent
    email_sent_date = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        """
        Make sure the saved email is lowercase
        """
        if self.email:
            self.email = self.email.lower()

        return super(ExternalInvite, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'inviter': user_to_dict(self.inviter),
            'invitee': self.to_user_dict(),
            'document': self.document.to_dict(include_analysis=False),
            'external': True,
        }

    def to_user_dict(self):
        return {
            'email': self.email,
            'username': self.email,
            'id': None,
            'job_title': None,
            'company': None,
            'avatar': '/static/img/mugpending.png',
            'first_name': None,
            'last_name': None,
            'pending': True,
            'last_login': None,
            'date_joined': None,
            'is_paid': False,
            'had_trial': False,
            'is_super': False,
            'tags': [],
            'keywords': [],
            'settings': None,
        }

    def create_collaboration_invite(self, user):
        from core.tools import disconnect_signal
        invite = CollaborationInvite(inviter=self.inviter, invitee=user, document=self.document)

        with disconnect_signal(models.signals.post_save, notify_collaboration_invite_creation, CollaborationInvite):
            invite.save()

        external_invite_transformed.send(sender=invite.__class__,
                                         external_invite=self,
                                         collaboration_invite=invite)

        self.pending = False
        self.email_sent_date = timezone.now()
        self.save()
        return invite

    def __unicode__(self):
        return self.email

    class Meta:
        ordering = ('-created',)


class DelayedNotification(TimeStampedModel):
    # A notifications.models.Notification missing some fields
    notification = PickledObjectField('Notification')

    # The missing fields, they will be filled with the new user {'fields': ['recipient', 'target']}
    user_fields = jsonfield.JSONField('Delayed fields', default={'fields': []})

    # The delayed user's email
    email = models.EmailField('Email')

    transient = models.BooleanField('Transient', default=True)

    @classmethod
    def delay_notification(cls, email, delayed_fields, **kwargs):
        notification = Notification()
        notification.actor = kwargs.get('actor')
        if kwargs.get('recipient') is not None:
            notification.recipient = kwargs.get('recipient')
        notification.verb = kwargs.get('verb')
        notification.target = kwargs.get('target')
        notification.action_object = kwargs.get('action_object')

        if kwargs.get('created') is not None:
            notification.created = kwargs.get('created')
        else:
            notification.created = datetime.datetime.now()

        data = {}
        if kwargs.get('render_string') is not None:
            data['render_string'] = kwargs.get('render_string')

        data['transient'] = kwargs.get('transient', True)

        if data:
            notification.data = data

        delayed_notif = DelayedNotification(notification=notification, email=email,
                                            transient=kwargs.get('transient', True))

        for df in delayed_fields:
            delayed_notif.add_delayed_field(df)

        delayed_notif.save()
        return delayed_notif

    def save(self, *args, **kwargs):
        """
        Make sure the email is lowercase
        """
        if self.email:
            self.email = self.email.lower()

        return super(DelayedNotification, self).save(*args, **kwargs)

    @property
    def delayed_fields(self):
        return self.user_fields['fields']

    def add_delayed_field(self, field_name):
        self.user_fields['fields'].append(field_name)

    def create_notification(self):
        """
        Create an actual notification from the serialized one saved in `notification` field
        """
        from core.tools import notification_url, notification_to_dict

        try:
            recipient = User.objects.get(email__iexact=self.email)
            for field_name in self.delayed_fields:
                setattr(self.notification, field_name, recipient)

            if not self.transient:
                self.notification.save()

            notif = self.notification
            notif_dict = notification_to_dict(notif)
            notif_dict['url'] = notification_url(notif)

            NotificationManager.create_user_message(recipient,
                                                    event_name='message',
                                                    message={
                                                        'notif': NotificationManager.ServerNotifications.ACTIVITY_UPDATE,
                                                        'activity_update': notif_dict}).send()

            return notif
        except User.DoesNotExist:
            return None
        except Exception:
            return None
        finally:
            self.delete()

    def __unicode__(self):
        return unicode(self.notification)


###############################################################################
#
#  Activity Updates
#
###############################################################################

@receiver(external_invite_transformed, sender=CollaborationInvite)
def notify_external_invite_transformed(sender, external_invite, collaboration_invite, **kwargs):
    from .tasks import store_activity_notification

    store_activity_notification.delay(
        actor=collaboration_invite.invitee,
        recipient=collaboration_invite.inviter,
        verb='joined',
        target=collaboration_invite.inviter,
        action_object=collaboration_invite.document,
        render_string="(actor) joined (target) on (action_object)",
        transient=False)

    store_activity_notification.delay(
        actor=collaboration_invite.invitee,
        recipient=collaboration_invite.invitee,
        verb='joined',
        target=collaboration_invite.inviter,
        action_object=collaboration_invite.document,
        render_string="(actor) joined (target) on (action_object)",
        transient=False)


@receiver(models.signals.post_save, sender=CollaborationInvite)
def notify_collaboration_invite_creation(sender, instance, *args, **kwargs):
    from .tasks import store_activity_notification
    if kwargs.get('created', False):
        store_activity_notification.delay(
            actor=instance.inviter,
            recipient=instance.invitee,
            verb='invited',
            target=instance.invitee,
            action_object=instance.document,
            render_string="(actor) invited (target) to collaborate on (action_object)",
            transient=False)


@receiver(sentence_liked, sender=Sentence)
def notify_sentence_liked(sender, **kwargs):
    from .tasks import store_activity_notification
    sentence = kwargs['sentence']
    user = kwargs['user']
    document = sentence.doc

    owner = document.owner
    all_users = set(document.collaborators + [owner])
    all_users.discard(user)

    for notified_user in all_users:
        store_activity_notification.delay(
            actor=user,
            recipient=notified_user,
            verb='liked',
            target=sentence,
            action_object=document,
            render_string="(actor) liked a clause on (action_object)",
            transient=False)


@receiver(sentence_disliked, sender=Sentence)
def notify_sentence_disliked(sender, **kwargs):
    from .tasks import store_activity_notification
    sentence = kwargs['sentence']
    user = kwargs['user']
    document = sentence.doc

    owner = document.owner
    all_users = set(document.collaborators + [owner])
    all_users.discard(user)

    for notified_user in all_users:
        store_activity_notification.delay(
            actor=user,
            recipient=notified_user,
            verb='liked',
            target=sentence,
            action_object=document,
            render_string="(actor) disliked a clause on (action_object)",
            transient=False)


@receiver(sentence_accepted, sender=Sentence)
def notify_sentence_accepted(sender, **kwargs):
    from .tasks import store_activity_notification
    sentence = kwargs['sentence']
    document = sentence.doc
    owner = document.owner
    all_users = set(document.collaborators)
    all_users.discard(owner)

    for notified_user in all_users:
        store_activity_notification.delay(
            actor=owner,
            recipient=notified_user,
            verb='accepted',
            target=sentence,
            action_object=document,
            render_string="(actor) accepted a clause on (action_object)",
            transient=False)


@receiver(sentence_rejected, sender=Sentence)
def notify_sentence_rejected(sender, **kwargs):
    from .tasks import store_activity_notification
    sentence = kwargs['sentence']
    document = sentence.doc
    owner = document.owner
    all_users = set(document.collaborators)
    all_users.discard(owner)

    for notified_user in all_users:
        store_activity_notification.delay(
            actor=owner,
            recipient=notified_user,
            verb='rejected',
            target=sentence,
            action_object=document,
            render_string="(actor) rejected a clause on (action_object)",
            transient=False)


@receiver(sentence_edited, sender=Sentence)
def notify_sentence_edited(sender, **kwargs):
    from .tasks import store_activity_notification
    sentence = kwargs['sentence']
    author = kwargs['author']
    document = sentence.doc

    owner = document.owner
    all_users = set(document.collaborators + [owner])
    all_users.discard(author)

    for notified_user in all_users:
        store_activity_notification.delay(
            actor=author,
            recipient=notified_user,
            verb='edited',
            target=sentence,
            action_object=document,
            render_string="(actor) edited a clause on (action_object)",
            transient=False)


###############################################################################
#
#  Various Notifications
#
###############################################################################

@receiver(user_logged_in, sender=User)
def notify_user_logged_in(sender, user, request, **kwargs):
    """
    Notify all the collaborators that a user logged in
    """
    NotificationManager.create_collaborators_message(
        user,
        event_name='message',
        message={
            'notif': NotificationManager.ServerNotifications.COLLABORATOR_LOGIN,
            'user': user_to_dict(user)
        }
    ).send()


@receiver(comment_posted, sender=Sentence)
def process_comment_posted(sender, **kwargs):
    logging.info('Received signal: process_comment_posted')
    from .tasks import store_activity_notification

    AFTER_INVITE_DELAY = 10  # seconds

    sentence = kwargs['sentence']
    author = kwargs['author']
    comment = kwargs['comment']
    created = kwargs.get('created')  # optional

    mentions = CommentType.extract_mentions(comment)

    logging.info('Mentions found: %s in %s', str(mentions), str(comment))

    try:
        sentence_index = sentence.doc.sentences_pks.index(sentence.pk)

        if CommentType.detect(mentions) == CommentType.BEAGLEBOT_REQUEST:
            ask_beagle.delay(comment, sentence, sentence_index, sentence.doc)

        for m in mentions:
            if m.lower() in CommentType.DefaultMentions.BEAGLEBOT:
                continue
            try:
                mentioned_user = User.objects.get(username=m)
            except User.DoesNotExist:
                logging.error('process_comment_posted: mention found, user could not be found: %s', str(m))
                continue

            # If user is already a collaborator, send mention email to him
            if sentence.doc.has_access(mentioned_user):
                try:
                    invite = CollaborationInvite.objects.get(
                        invitee=mentioned_user, document=sentence.doc)
                except CollaborationInvite.DoesNotExist:
                    invite = None
                except CollaborationInvite.MultipleObjectsReturned:
                    invite = CollaborationInvite.objects.filter(
                        invitee=mentioned_user, document=sentence.doc
                    ).order_by('created')[0]

                def send_mention_email(author, mentioned_user, sentence):
                    logging.info('process_comment_posted: sending mention email to %s' % str(mentioned_user))
                    from core.tasks import send_user_was_mentioned
                    send_user_was_mentioned.delay(author.pk, mentioned_user.pk,
                                                  sentence.pk, sentence_index)

                # Don't send mention email if user was just invited
                if invite:
                    invite_timedelta = (timezone.now() - invite.created).seconds
                    if invite_timedelta > AFTER_INVITE_DELAY:
                        send_mention_email(author, mentioned_user, sentence)

                # Document's owner was mentioned
                elif mentioned_user.pk == sentence.doc.owner.pk:
                    send_mention_email(author, mentioned_user, sentence)


            logging.info('process_comment_posted: storing new mention notification: %s', str(mentioned_user))

            store_activity_notification.delay(
                actor=author,
                recipient=mentioned_user,
                verb='mentioned',
                target=mentioned_user,
                action_object=sentence,
                render_string="(actor) mentioned (target) in a comment on (action_object)",
                transient=False,
                created=created)

    except ValueError:
        pass


@receiver(document_owner_changed, sender=Document)
def process_document_owner_changed(sender, **kwargs):
    """ Send the document owner changed email """
    from core.tasks import send_owner_changed

    old_owner = kwargs['before_owner']
    document = kwargs['document']

    send_owner_changed.delay(old_owner.pk, document.pk)


@receiver(collaboration_invite_pre_delete, sender=CollaborationInvite)
def process_collaboration_invite_delete(sender, **kwargs):
    from core.tasks import store_activity_notification

    invite = kwargs['instance']
    actor = kwargs['request_user']
    action_object = invite.document

    # Need to be able to distinguish if it's owner deleting invite or it's the invited user
    if action_object.owner == actor:
        recipient = invite.invitee
        target = invite.invitee
        verb = 'revoked'
        render_string = "(actor) revoked access from (target) to collaborate on (action_object)"
    else:
        recipient = invite.inviter
        target = invite.inviter
        verb = 'rejected'
        render_string = "(actor) rejected invite from (target) to collaborate on (action_object)"

        # Actor isn't interested anymore in notifications where target invited him/her to
        # collaborate on action_object
        Notification.objects.filter(
            actor_object_id=target.id, verb='invited',
            target_object_id=actor.id, action_object_object_id=action_object.id
        ).delete()

    store_activity_notification.delay(
        actor=actor,
        recipient=recipient,
        verb=verb,
        target=target,
        action_object=action_object,
        render_string=render_string,
        transient=False
    )

# Change Batch owner if all documents in a Batch belong to same owner
# (but different from Batch owner)
@receiver(post_save, sender=Document)
def check_batch_owner(sender, **kwargs):
    doc = kwargs['instance']
    batch = doc.batch
    if batch and doc.owner != batch.owner:
        owner_change = True
        for d in batch.document_set.only('owner'):
            if d.owner != doc.owner:
                # Not all documents belong to same user
                owner_change = False
                break

        if owner_change:
            batch.owner = doc.owner
            batch.save()
