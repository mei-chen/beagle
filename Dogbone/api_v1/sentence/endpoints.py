import json
import logging

from django.db import transaction, DatabaseError
from django.conf import settings

from dogbone.actions import has_permission

from core.tools import user_to_dict
from core.tasks import mark_as_read_sentence_related_notifications
from core.models import Sentence, Document, SentenceLock, SentenceAnnotations

from beagle_simpleapi.endpoint import ListView, DetailView, ActionView
from beagle_simpleapi.mixin import DeleteDetailModelMixin, PutDetailModelMixin

from beagle_realtime.notifications import NotificationManager

from ml.tasks import (
    onlinelearner_train_task, onlinelearner_removesample_task, onlinelearner_negative_train_task,
    spot_experiment_accept_sentence, spot_experiment_reject_sentence,
)


class SentenceMixin(object):
    def get_object(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")
        sentence = self.get_sentence(request, *args, **kwargs)
        return sentence

    def has_access(self, instance):
        return (not self.document.trash) and (self.document.has_access(self.user) or self.user.is_superuser)

    def get_document(self, request, *args, **kwargs):
        try:
            document = Document.ready_objects.get(trash=False, uuid=kwargs['uuid'])
            if not document.has_access(self.user):
                return None
            return document
        except Document.DoesNotExist:
            return None

    def get_sentence_index(self, request, *args, **kwargs):
        return int(kwargs['s_idx'])

    def get_sentence(self, request, *args, **kwargs):
        try:
            self.sentence_index = self.get_sentence_index(request, *args, **kwargs)
            self.sentence_pk = self.document.sentences_pks[self.sentence_index]
            return Sentence.objects.get(pk=self.sentence_pk)
        except (IndexError, Sentence.DoesNotExist, KeyError):
            raise self.NotFoundException("Sentence not found")

    def send_notification(self, sentence_idx, sentence, notif_type=NotificationManager.ServerNotifications.DOCUMENT_CHANGED_NOTIFICATION):
        document = sentence.doc
        payload = {
            'sentenceIdx': sentence_idx,
            'sentence': sentence.to_dict(),
            'user': {
                'email': self.user.email,
                'username': self.user.username,
                'id': self.user.id
            },
            'notif': notif_type
        }

        msg = NotificationManager.create_document_message(document, 'message', payload)
        msg.send()


class SentenceDetailView(SentenceMixin, DetailView, DeleteDetailModelMixin, PutDetailModelMixin):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)$'
    endpoint_name = 'sentence_detail_view'

    def delete_model(self, model, request, *args, **kwargs):
        sentence = self.document.delete_sentence(model, self.user)
        return sentence

    def validate_put(self, item, request, *args, **kwargs):
        if 'text' not in item and 'annotations' not in item:
            raise self.BadRequestException("No data provided to modify the sentence.")
        if 'accepted' in item or 'rejected' in item:
            raise self.BadRequestException("Use specific endpoints for accepting or rejecting a sentence")
        return True

    def save_model(self, model, data, request, *args, **kwargs):
        new_sentence = model.edit(
                self.user,
                text=data.get('text', None),
                annotations=data.get('annotations', None),
                reanalyze=data.get('reanalyze', False),
            )

        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               new_sentence)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, model.pk)

        return new_sentence


class SentenceAcceptActionView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/accept$'
    endpoint_name = 'sentence_accept_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        allow, _ = has_permission(request, 'accept_changes')
        if not allow:
            logging.warning('%s tried to accept changes without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to accept changes with your subscription")

        new_sentence = self.instance.accept(self.user)
        self.document.update_sentence(self.instance, new_sentence)
        self.document.save()
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               new_sentence)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return self.to_dict(new_sentence)


class SentenceRejectActionView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/reject'
    endpoint_name = 'sentence_reject_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        allow, _ = has_permission(request, 'reject_changes')
        if not allow:
            logging.warning('%s tried to reject changes without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to reject changes with your subscription")

        new_sentence = self.instance.reject(self.user)
        self.document.update_sentence(self.instance, new_sentence)
        self.document.save()
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               new_sentence)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return self.to_dict(new_sentence)


class SentenceUndoActionView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/undo'
    endpoint_name = 'sentence_undo_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        new_sentence = self.instance.undo(self.user)
        self.document.update_sentence(self.instance, new_sentence)
        self.document.save()
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               new_sentence)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return self.to_dict(new_sentence)


class SentenceLikeActionView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/like$'
    endpoint_name = 'sentence_like_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        allow, _ = has_permission(request, 'like', document=self.document)
        if not allow:
            logging.warning('%s tried to like without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to like with your subscription")

        self.instance.like(self.user)
        self.document.invalidate_cache()
        self.document.save()

        # Also send socket notification for everybody else to receive changes
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               self.instance)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return self.to_dict(self.instance)

    def delete(self, request, *args, **kwargs):
        self.instance = self.get_object(request, *args, **kwargs)

        allow, _ = has_permission(request, 'like', document=self.document)
        if not allow:
            logging.warning('%s tried to like without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to like with your subscription")

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        sentence_idx = self.get_sentence_index(request, *args, **kwargs)
        success = self.instance.remove_like(request.user)
        if success:
            # Also send socket notif for everybody else to receive changes
            self.send_notification(sentence_idx, self.instance)

            # Mark the Notifications related to this sentence as read
            mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

            return {'status': 1, 'message': "OK"}
        else:
            return {'status': 0, 'message': "Cannot delete like. Like probably not present"}


class SentenceDislikeActionView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/dislike$'
    endpoint_name = 'sentence_dislike_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        allow, _ = has_permission(request, 'dislike', document=self.document)
        if not allow:
            logging.warning('%s tried to dislike without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to dislike with your subscription")

        self.instance.dislike(self.user)
        self.document.invalidate_cache()
        self.document.save()

        # Also send socket notif for everybody else to receive changes
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               self.instance)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return self.to_dict(self.instance)

    def delete(self, request, *args, **kwargs):
        self.instance = self.get_object(request, *args, **kwargs)

        allow, _ = has_permission(request, 'dislike', document=self.document)
        if not allow:
            logging.warning('%s tried to dislike without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to dislike with your subscription")

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        sentence_idx = self.get_sentence_index(request, *args, **kwargs)
        success = self.instance.remove_dislike(request.user)
        if success:
            # Also send socket notif for everybody else to receive changes
            self.send_notification(sentence_idx, self.instance)

            # Mark the Notifications related to this sentence as read
            mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

            return {'status': 1, 'message': "OK"}
        else:
            return {'status': 0, 'message': "Cannot delete dislike. Dislike probably not present"}


class SentenceTagsView(SentenceMixin, ActionView):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/tags$'
    endpoint_name = 'sentence_tags_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        """ Expects a key/value pair like {'tag': 'label'} """
        allow, _ = has_permission(request, 'add_tag', document=self.document)
        if not allow:
            logging.warning('%s tried to add a tag without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to add a tag with your subscription")

        data = json.loads(request.body)

        if 'tag' not in data:
            return {'status': 0, 'message': "Please provide key/value pair {'tag' : 'label'}"}

        # Add the manual tag to the sentence
        label = data['tag']

        # Get optional parameters
        sublabel = data.get('sublabel', None)
        party = data.get('party', None)
        atype = data.get('type', SentenceAnnotations.MANUAL_TAG_TYPE)

        self.instance.add_tag(user=self.user,
                              label=label,
                              sublabel=sublabel,
                              party=party,
                              approved=(atype != SentenceAnnotations.SUGGESTED_TAG_TYPE),
                              annotation_type=atype)

        # Also add it to user-level tags cache (used for typeahead suggestions)
        self.user.details.add_tag(label)

        # Train the appropriate Online Learner
        onlinelearner_train_task.delay(label, self.user, self.instance, kwargs['s_idx'])

        # Also send socket notif for everybody else to receive changes
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               self.instance)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return {'status': 1, 'message': "OK"}

    def delete(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)

        if self.document is None:
            raise self.NotFoundException("Document not found")

        allow, _ = has_permission(request, 'delete_tag', document=self.document)
        if not allow:
            logging.warning('%s tried to delete a tag without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to delete a tag with your subscription")

        data = json.loads(request.body)
        if 'tag' not in data:
            return {'status': 0, 'message': "Please provide tag"}

        self.instance = self.get_object(request, *args, **kwargs)

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        sentence_idx = self.get_sentence_index(request, *args, **kwargs)
        label = data['tag']

        # Get optional parameters
        sublabel = data.get('sublabel', None)
        party = data.get('party', None)
        atype = data.get('type', None)

        # Remove the tag from the sentence object
        annotation = self.instance.remove_tag(user=request.user,
                                              label=label,
                                              sublabel=sublabel,
                                              party=party)

        if annotation:
            if atype == SentenceAnnotations.MANUAL_TAG_TYPE:
                # Remove the sample and retrain the appropriate Online Learner
                onlinelearner_removesample_task.delay(label, request.user, self.instance, kwargs['s_idx'])

            elif atype == SentenceAnnotations.SUGGESTED_TAG_TYPE:
                experiment_uuid = annotation.get('experiment_uuid')
                if experiment_uuid:
                    # Reject the tag suggested by the Spot experiment
                    spot_experiment_reject_sentence.delay(experiment_uuid, self.instance)
                else:
                    # Train the appropriate Online Learner with neg sample
                    onlinelearner_negative_train_task.delay(label, request.user, self.instance, kwargs['s_idx'])

            # Also send socket notif for everybody else to receive changes
            self.send_notification(sentence_idx, self.instance)

            # Mark the Notifications related to this sentence as read
            mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

            return {'status': 1, 'message': "OK"}
        else:
            return {'status': 0, 'message': "Cannot delete tag"}


class SentenceSuggestedTagsView(SentenceMixin, ActionView, PutDetailModelMixin):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/sugg_tags$'
    endpoint_name = 'sentence_sugg_tags_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def action(self, request, *args, **kwargs):
        """ Expects a list of suggested tags as {'tag': 'tag1'} """
        data = json.loads(request.body)
        if 'tag' not in data:
            return {'status': 0, 'message': "Please provide tags"}

        # Add the manual tag to the sentence
        label = data['tag']

        # Get optional parameters
        sublabel = data.get('sublabel', None)
        party = data.get('party', None)
        atype = data.get('type', SentenceAnnotations.SUGGESTED_TAG_TYPE)
        approved = data.get('approved', False)

        self.instance.add_tag(user=self.user,
                              label=label,
                              sublabel=sublabel,
                              party=party,
                              approved=approved,
                              annotation_type=atype)

        # Also add it to user-level tags cache (used for typeahead suggestions)
        self.user.details.add_tag(label)

        # Also send socket notification for everybody else to receive changes
        self.send_notification(self.get_sentence_index(request, *args, **kwargs),
                               self.instance)

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return {'status': 1, 'message': "OK"}

    def delete(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")

        data = json.loads(request.body)
        if 'tag' not in data:
            return {'status': 0, 'message': "Please provide tags"}

        self.instance = self.get_object(request, *args, **kwargs)

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        sentence_idx = self.get_sentence_index(request, *args, **kwargs)
        label = data['tag']

        # Get optional parameters
        sublabel = data.get('sublabel', None)
        party = data.get('party', None)

        # Remove the tag from the sentence object
        annotation = self.instance.remove_tag(user=request.user,
                                              label=label,
                                              sublabel=sublabel,
                                              party=party)

        if annotation:
            experiment_uuid = annotation.get('experiment_uuid')
            if experiment_uuid:
                # Reject the tag suggested by the Spot experiment
                spot_experiment_reject_sentence.delay(experiment_uuid, self.instance)
            else:
                # Train the appropriate Online Learner with neg sample
                onlinelearner_negative_train_task.delay(label, request.user, self.instance, kwargs['s_idx'])

            # Also send socket notif for everybody else to receive changes
            self.send_notification(sentence_idx, self.instance)

            # Mark the Notifications related to this sentence as read
            mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

            return {'status': 1, 'message': "OK"}

        return {'status': 0, 'message': "Cannot delete suggested tag"}

    def put(self, request, *args, **kwargs):
        """ Approves a suggested tag, turning it into a 'regular' tag """
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")

        data = json.loads(request.body)
        if 'tag' not in data:
            return {'status': 0, 'message': "Please provide tags"}

        self.instance = self.get_object(request, *args, **kwargs)
        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        label = data['tag']

        # Get optional parameters
        sublabel = data.get('sublabel', None)
        party = data.get('party', None)

        # Remove the tag from the sentence object
        annotation = self.instance.remove_tag(user=request.user,
                                              label=label,
                                              sublabel=sublabel,
                                              party=party)

        if not annotation:
            return {'status': 0, 'message': "Cannot delete suggested tag"}

        classifier_id = annotation.get('classifier_id')
        experiment_uuid = annotation.get('experiment_uuid')

        # Add (approved) tag back to the sentence's list of tags
        self.instance.add_tag(user=self.user,
                              label=label,
                              sublabel=sublabel,
                              party=party,
                              annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                              classifier_id=classifier_id,
                              experiment_uuid=experiment_uuid,
                              approved=True)

        # Also add it to user-level tags cache (used for typeahead suggestions)
        self.user.details.add_tag(label)

        if experiment_uuid:
            # Accept the tag suggested by the Spot experiment
            spot_experiment_accept_sentence.delay(label, experiment_uuid, self.instance, kwargs['s_idx'])
        else:
            # Train the appropriate Online Learner
            onlinelearner_train_task.delay(label, self.user, self.instance, kwargs['s_idx'])

        # Also send socket notification for everybody else to receive changes
        self.send_notification(
            self.get_sentence_index(request, *args, **kwargs),
            self.instance
        )

        # Mark the Notifications related to this sentence as read
        mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

        return {'status': 1, 'message': "OK"}


class SentenceBulkTagsView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/tags$'
    endpoint_name = 'sentence_bulk_tags_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def send_notification(self, sentence_idx, sentence):
        document = sentence.doc
        payload = {
            'sentenceIdx': sentence_idx,
            'sentence': sentence.to_dict(),
            'user': {
                'email': self.user.email,
                'username': self.user.username,
                'id': self.user.id
            },
            'notif': NotificationManager.ServerNotifications.DOCUMENT_CHANGED_NOTIFICATION
        }

        msg = NotificationManager.create_document_message(document, 'message', payload)
        msg.send()

    def send_generic_notification(self, document, payload):
        msg = NotificationManager.create_document_message(document, 'message', payload)
        msg.send()

    def action(self, request, *args, **kwargs):
        """ Expects a json in this format:
        TODO: add sample
        """
        data = json.loads(request.body)

        if 'sentences' not in data:
            return {'status': 0, 'message': "Please provide a list of sentences with a list of tags"}

        response = {'sentences': []}
        payload = {
            'sentences': [],
            'documentUUID': kwargs['uuid'],
            'notif': NotificationManager.ServerNotifications.DOCUMENT_BULK_TAGS_CREATED_NOTIFICATION
        }
        for sentence_instance in data['sentences']:
            try:
                sentence_idx = int(sentence_instance['sentenceIdx'])
            except ValueError:
                logging.error('Invalid sentenceIdx in SentenceBulkTagsView sentenceIdx=%s', sentence_instance['sentenceIdx'])
                continue

            annotations = sentence_instance['annotations']

            sentence = self.instance.get_sentence_by_index(sentence_idx)
            if sentence is None:
                logging.error('Sentence not found in SentenceBulkTagsView sentenceIdx=%s', sentence_idx)
                continue

            for ann in annotations:
                # Get parameters
                label = ann.get('label', None)
                sublabel = ann.get('sublabel', None)
                party = ann.get('party', None)
                atype = ann.get('type', None)

                sentence.add_tag(request.user,
                                 label=label,
                                 sublabel=sublabel,
                                 party=party,
                                 approved=(atype != SentenceAnnotations.SUGGESTED_TAG_TYPE),
                                 annotation_type=atype)

                self.user.details.add_tag(label)

                onlinelearner_train_task.delay(label, self.user, sentence, sentence_idx)

            response['sentences'].append(sentence_instance)
            payload['sentences'].append(sentence.to_dict())

        self.send_generic_notification(self.instance, payload)
        return response

    def delete(self, request, *args, **kwargs):
        self.instance = self.get_object(request, *args, **kwargs)

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        if self.instance is None:
            raise self.NotFoundException("Document not found")

        data = json.loads(request.body)

        if 'sentences' not in data:
            return {'status': 0, 'message': "Please provide a list of sentences with a list of tags"}

        response = {'sentences': []}
        payload = {
            'sentences': [],
            'documentUUID': kwargs['uuid'],
            'notif': NotificationManager.ServerNotifications.DOCUMENT_BULK_TAGS_DELETED_NOTIFICATION
        }

        for sentence_instance in data['sentences']:
            try:
                sentence_idx = int(sentence_instance['sentenceIdx'])
            except ValueError:
                logging.error('Invalid sentenceIdx in SentenceBulkTagsView sentenceIdx=%s', sentence_instance['sentenceIdx'])
                continue

            annotations = sentence_instance['annotations']

            sentence = self.instance.get_sentence_by_index(sentence_idx)
            if sentence is None:
                logging.error('Sentence not found in SentenceBulkTagsView sentenceIdx=%s', sentence_idx)
                continue

            not_found_annotations = []

            for annotation in annotations:
                # Get parameters
                label = annotation.get('label', None)
                sublabel = annotation.get('sublabel', None)
                party = annotation.get('party', None)
                atype = annotation.get('type', SentenceAnnotations.MANUAL_TAG_TYPE)

                annotation_full = sentence.remove_tag(request.user,
                                                      label=label,
                                                      sublabel=sublabel,
                                                      party=party)

                if annotation_full:
                    if atype == SentenceAnnotations.SUGGESTED_TAG_TYPE:
                        experiment_uuid = annotation_full.get('experiment_uuid')
                        if experiment_uuid:
                            # Reject the tag suggested by the Spot experiment
                            spot_experiment_reject_sentence.delay(experiment_uuid, sentence)
                        else:
                            onlinelearner_negative_train_task.delay(label, request.user, sentence, sentence_idx)
                    else:
                        onlinelearner_removesample_task.delay(label, request.user, sentence, sentence_idx)
                else:
                    not_found_annotations.append(annotation)

            # Update the sentence instance to remove all not-found annotations
            for annotation in not_found_annotations:
                sentence_instance['annotations'].remove(annotation)

            response['sentences'].append(sentence_instance)
            payload['sentences'].append(sentence.to_dict())

        self.send_generic_notification(self.instance, payload)
        return response

    def put(self, request, *args, **kwargs):
        """
        Use this for suggested tags.
        Bulk approve action, turning them into 'regular' tags
        """
        self.instance = self.get_object(request, *args, **kwargs)

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        if self.instance is None:
            raise self.NotFoundException("Document not found")

        data = json.loads(request.body)

        if 'sentences' not in data:
            return {'status': 0, 'message': "Please provide a list of sentences with a list of tags"}

        response = {'sentences': []}
        payload = {
            'sentences': [],
            'documentUUID': kwargs['uuid'],
            'notif': NotificationManager.ServerNotifications.DOCUMENT_BULK_TAGS_UPDATED_NOTIFICATION
        }

        for sentence_instance in data['sentences']:
            try:
                sentence_idx = int(sentence_instance['sentenceIdx'])
            except ValueError:
                logging.error('Invalid sentenceIdx in SentenceBulkTagsView sentenceIdx=%s', sentence_instance['sentenceIdx'])
                continue

            annotations = sentence_instance['annotations']

            sentence = self.instance.get_sentence_by_index(sentence_idx)
            if sentence is None:
                logging.error('Sentence not found in SentenceBulkTagsView sentenceIdx=%s', sentence_idx)
                continue

            for annotation in annotations:
                # Get parameters
                label = annotation.get('label', None)
                sublabel = annotation.get('sublabel', None)
                party = annotation.get('party', None)

                annotation_full = sentence.remove_tag(request.user,
                                                      label=label,
                                                      sublabel=sublabel,
                                                      party=party)

                if not annotation_full:
                    return {'status': 0, 'message': "Cannot delete suggested tag"}

                classifier_id = annotation_full.get('classifier_id')
                experiment_uuid = annotation_full.get('experiment_uuid')

                # Add (approved) tag back to the sentence's list of tags
                sentence.add_tag(user=self.user,
                                 label=label,
                                 sublabel=sublabel,
                                 party=party,
                                 annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                                 classifier_id=classifier_id,
                                 experiment_uuid=experiment_uuid,
                                 approved=True)

                # Also add it to user-level tags cache (used for typeahead suggestions)
                self.user.details.add_tag(label)

                if experiment_uuid:
                    # Accept the tag suggested by the Spot experiment
                    spot_experiment_accept_sentence.delay(label, experiment_uuid, sentence, sentence_idx)
                else:
                    # Train the appropriate Online Learner
                    onlinelearner_train_task.delay(label, request.user, sentence, sentence_idx)

            response['sentences'].append(sentence_instance)
            payload['sentences'].append(sentence.to_dict())

        self.send_generic_notification(self.instance, payload)

        return response


class SentenceHistoryListView(ListView, SentenceMixin):
    """
    TODO: Test this endpoint
    TODO: Check permissions on the document
    """
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/history$'
    endpoint_name = 'sentence_history_list_view'

    def get_steps(self, request, *args, **kwargs):
        try:
            return int(request.GET['steps'])
        except (ValueError, KeyError):
            return 1

    def get_list(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        self.sentence = self.get_sentence(request, *args, **kwargs)

        steps = self.get_steps(request, *args, **kwargs)

        version = self.sentence
        history = []
        for i in range(abs(steps)):
            if not version:
                break
            else:
                history.append(version)
            if steps > 0:
                version = version.next_revision
            else:
                version = version.prev_revision
        return history


class SentenceCommentsListView(ListView, SentenceMixin):
    model = Sentence
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/comments'
    endpoint_name = 'sentence_comments_list_view'

    DEFAULT_RESULTS_PER_PAGE = settings.COMMENTS_PER_PAGE

    @classmethod
    def to_dict(cls, model):
        """
        No serialization needed
        """
        return model

    def init_data(self, request, *args, **kwargs):
        """
        Init document and sentence models and attach them to the endpoint object
        """
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")

        self.sentence = self.get_sentence(request, *args, **kwargs)
        if self.sentence is None:
            raise self.NotFoundException("Sentence not found")

    def get_list(self, request, *args, **kwargs):
        self.init_data(request, *args, **kwargs)
        if self.sentence.comments is None:
            return []

        comments = self.sentence.comments['comments'][self.get_slice()]
        comments.reverse()
        return [Sentence.expand_comment_dict(comment, self.sentence, self.document)
                for comment in comments]

    def send_comment_notification(self, comment_dict):
        """
        Create a comment notification payload and send it to REDIS
        :param comment_dict: expanded comment dict (expanded using Sentence.expand_comment_dict)
        :return:
        """
        notification_payload = {
            'comment': comment_dict.copy(),
            'notif': NotificationManager.ServerNotifications.COMMENT_ADDED_NOTIFICATION,
            'sentence': self.sentence.to_dict(),
        }
        notification_payload['sentence']['idx'] = self.sentence_index

        NotificationManager.create_document_message(self.document, 'message',
                                                    notification_payload).send()

        return notification_payload

    def post(self, request, *args, **kwargs):
        """
        Add a new comment
        Expected input data:
        {'message': "..."} or a list of [{'message': "..."}, ...]
        """
        self.init_data(request, *args, **kwargs)
        allow, _ = has_permission(request, 'comment', document=self.document)
        if not allow:
            logging.warning('%s tried to comment without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to comment with your subscription")

        try:
            self.model_data = json.loads(request.body)
            if isinstance(self.model_data, dict):
                self.model_data = [self.model_data]

            instances = []
            for item in self.model_data:
                comment_dict = Sentence.expand_comment_dict(
                        self.sentence.add_comment(self.user, item['message']).copy(),
                        self.sentence,
                        self.document)

                if comment_dict:
                    # SocketIO notification
                    self.send_comment_notification(comment_dict)

                    # Add the newly created comment to the response
                    instances.append(self.to_dict(comment_dict))

                    # Mark the Notifications related to this sentence as read
                    mark_as_read_sentence_related_notifications.delay(self.user.pk, self.sentence.pk)

            return instances
        except Exception as e:
            logging.error('Exception encountered in SentenceCommentsListView POST: %s', str(e))
            raise e

    def delete(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)

        allow, _ = has_permission(request, 'comment', document=self.document)
        if not allow:
            logging.warning('%s tried to comment without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to comment with your subscription")

        if self.document is None:
            raise self.NotFoundException("Document not found")

        data = json.loads(request.body)
        if 'comment_uuid' not in data:
            return {'status': 0, 'message': "Please provide a comment UUID"}

        self.instance = self.get_object(request, *args, **kwargs)

        if not self.has_access(self.instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        sentence_idx = self.get_sentence_index(request, *args, **kwargs)
        # sentence = Sentence.objects.get(pk=self.document.sentences_pks[sentence_idx])
        success = self.instance.remove_comment(request.user, data['comment_uuid'])
        if success:
            # Also send socket notif for everybody else to receive changes
            self.send_notification(sentence_idx, self.instance)

            # Mark the Notifications related to this sentence as read
            mark_as_read_sentence_related_notifications.delay(self.user.pk, self.instance.pk)

            return {'status': 1, 'message': "OK"}
        else:
            return {'status': 0, 'message': "Cannot delete comment"}


class SentenceLockDetailView(DetailView, SentenceMixin):
    model = SentenceLock
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/(?P<s_idx>[0-9]+)/lock'
    endpoint_name = 'sentence_lock_detail_view'

    def sentence_lock_response(self, sentence_index, sentence, response,
            code=None, error=None):
        """
        Wraps the JSON responses in this View to add some information that
        should be present in every response. Didn't want to override
        `wrap_result` since the sentence object would need to be retreived from
        the index from the document which would need to be retrieved... and the
        sentence is retrieved with the `select_for_update` command, so it
        wouldn't have the same behaviour.
        """
        owner = sentence.lock_owner
        base_response = {
            'docUUID': sentence.doc.uuid,
            'owner': user_to_dict(owner) if owner is not None else None,
            'sentenceIdx': sentence_index,
            'sentence': sentence.to_dict()
        }
        # add keys from `response` to `base_response`
        base_response.update(response)
        if code is not None:
            base_response['http_status'] = code
            base_response['error'] = error
        return base_response

    def get(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")
        with transaction.atomic():
            try:
                sentence_idx = self.get_sentence_index(request, *args, **kwargs)
                sentence = Sentence.objects.select_for_update(nowait=True).get(
                    pk=self.document.sentences_pks[sentence_idx])
                return self.sentence_lock_response(sentence_idx, sentence, {
                    'isLocked': sentence.is_locked,
                })
            except DatabaseError:
                raise self.BadRequestException("Could not acquire transaction")

    def put(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")

        with transaction.atomic():
            try:
                sentence_idx = self.get_sentence_index(request, *args, **kwargs)
                sentence = Sentence.objects.select_for_update(nowait=True).get(
                    pk=self.document.sentences_pks[sentence_idx])
                try:
                    # If sentence already has a lock, return sentence instance, no need to throw the error
                    if not sentence.lock:
                        sentence.acquire_lock(request.user)
                        self.send_notification(
                            sentence_idx,
                            sentence,
                            notif_type=NotificationManager.ServerNotifications.DOCUMENT_LOCK_CHANGED_NOTIFICATION
                        )

                        # Mark the Notifications related to this sentence as read
                        mark_as_read_sentence_related_notifications.delay(self.user.pk, sentence.pk)
                        return self.sentence_lock_response(sentence_idx, sentence, {'success': True})

                    # Of owner is not requester return error.
                    elif sentence.lock.owner != request.user:
                        return self.sentence_lock_response(sentence_idx, sentence, {
                            'success': False,
                        }, code=403, error=str("Not owner so can't update"))

                    return self.sentence_lock_response(sentence_idx, sentence, {'success': True})

                except SentenceLock.SentenceLockException as e:
                    return self.sentence_lock_response(sentence_idx, sentence, {
                        'success': False,
                    }, code=403, error=str(e))
            except DatabaseError:
                raise self.UnauthorizedException("Could not acquire lock")

    def delete(self, request, *args, **kwargs):
        self.document = self.get_document(request, *args, **kwargs)
        if self.document is None:
            raise self.NotFoundException("Document not found")

        with transaction.atomic():
            try:
                sentence_idx = self.get_sentence_index(request, *args, **kwargs)
                sentence = Sentence.objects.select_for_update(nowait=True).get(
                    pk=self.document.sentences_pks[sentence_idx])
                try:
                    if request.user == sentence.lock_owner:
                        sentence.release_lock()
                        self.send_notification(
                            sentence_idx,
                            sentence,
                            notif_type=NotificationManager.ServerNotifications.DOCUMENT_LOCK_CHANGED_NOTIFICATION
                        )
                        return self.sentence_lock_response(sentence_idx, sentence, {
                            'success': True,
                        })
                    else:
                        msg = "Cannot delete lock you do not own"
                        return self.sentence_lock_response(sentence_idx, sentence, {
                            'success': False,
                        }, code=403, error=msg)
                except SentenceLock.SentenceLockException as e:
                    return self.sentence_lock_response(sentence_idx, sentence, {
                        'success': False,
                    }, code=400, error=str(e))
            except DatabaseError:
                raise self.UnauthorizedException("Could not release lock")
