import json
import os
import requests
import urllib
import uuid

from base64 import b64decode
from constance import config

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now

from beagle_simpleapi.endpoint import DetailView, ListView, ComputeView, StatusView
from beagle_simpleapi.mixin import PutDetailModelMixin
from dogbone.app_settings.marketing_settings import TrialSubscription
from portal.models import UserProfile
from core.tools import user_to_dict
from core.models import CollaboratorList, ExternalInvite, Batch, Document, UserLastViewDate, SentenceAnnotations
from portal.tasks import hubspot_update_contact_properties
from utils.django_utils.query import get_user_by_identifier
from marketing.models import PurchasedSubscription
from integrations.s3 import get_s3_bucket_manager
from authentication.models import AuthToken


class CurrentUserDetailView(DetailView, PutDetailModelMixin):
    model = User
    url_pattern = r'/user/me$'
    endpoint_name = 'me_detail_view'

    @classmethod
    def to_dict(cls, model):
        user = user_to_dict(model)

        # attach the token info
        try:
            model.auth_token
        except AuthToken.DoesNotExist:
            AuthToken.create_token_model(model)

        user.update({
            'token': model.auth_token.token,
            'token_expire': str(model.auth_token.key_expire) if model.auth_token.key_expire else None
        })
        return user

    def get_object(self, request, *args, **kwargs):
        return request.user

    def save_model(self, model, data, request, *args, **kwargs):
        properties = []

        old_pass = data.get('password')
        new_pass = data.get('new_password')
        confirm_pass = data.get('confirm_password')
        if old_pass or not model.password:
            if not new_pass or new_pass != confirm_pass:
                raise self.BadRequestException()
            if model.password and not model.check_password(old_pass):
                raise self.UnauthorizedException("Old password doesn't match")

            model.set_password(new_pass)

        if 'first_name' in data and data['first_name'] and data['first_name'] != request.user.first_name:
            model.first_name = data['first_name']
            properties.append({'property': 'firstname', 'value': data['first_name']})

        if 'last_name' in data and data['last_name'] and data['last_name'] != request.user.last_name:
            model.last_name = data['last_name']
            properties.append({'property': 'lastname', 'value': data['last_name']})

        if 'phone' in data and data['phone'] and data['phone'] != request.user.details.phone:
            model.details.phone = data['phone']
            properties.append({'property': 'phone', 'value': data['phone']})

        if 'job_title' in data and data['job_title'] and data['job_title'] != request.user.details.job_title:
            model.details.job_title = data['job_title']
            properties.append({'property': 'jobtitle', 'value': data['job_title']})

        if 'company' in data and data['company'] and data['company'] != request.user.details.company:
            model.details.company = data['company']
            properties.append({'property': 'company', 'value': data['company']})

        if 'avatar' in data and data['avatar'] and data['avatar'] != request.user.details.avatar:
            data = b64decode(data['avatar'].split(",")[1])
            filename = str(uuid.uuid4()) + '.png'
            s3manager = get_s3_bucket_manager(settings.PROFILE_PICTURE_BUCKET)
            today = now().date()
            s3key = "profile_photo/%s/%s/%s/%s" % (today.year, today.month, today.day, filename)
            s3manager.save_string(s3key, data, acl='public-read')
            model.details.avatar_s3 = '%s:%s' % (settings.PROFILE_PICTURE_BUCKET, s3key)

        # Send update to hubspot if Prod and changes have been made
        if len(properties) > 0 and settings.DEBUG is False:
            hubspot_update_contact_properties.delay(request.user.email, properties)

        model.details.save()
        model.save()
        return model


class UserDetailView(DetailView):
    model = User
    url_pattern = r'/user/(?P<identifier>[a-zA-Z0-9\-\+_@%\.]+)$'
    endpoint_name = 'user_detail_view'

    @classmethod
    def to_dict(cls, model):
        return user_to_dict(model)

    def get_object(self, request, *args, **kwargs):
        try:
            identifier = urllib.unquote(kwargs['identifier'])
        except KeyError:
            raise self.BadRequestException("Please provide a valid identifier")

        # First try to retrieve the user by ID
        user = get_user_by_identifier(identifier)
        if user is None:
            raise self.NotFoundException("This username does not exist")

        return user


class UserUnviewedDocsView(UserDetailView):
    """
    Displays which documents were never read by specific user.

    Format is: [document1.uuid, document2.uuid]
    """

    url_pattern = r'/user/(?P<identifier>[a-zA-Z0-9\-\+_@%\.]+)/unviewed_docs$'
    endpoint_name = 'user_unviewed_docs_view'

    @classmethod
    def to_dict(cls, model):
        viewdates = UserLastViewDate.objects.filter(user=model).only('document')
        viewed_docs = [vd.document for vd in viewdates]
        all_docs = Document.get_aggregated_documents(model)

        return [doc.uuid for doc in all_docs if doc not in viewed_docs]


class UserAuthenticationView(ComputeView):
    url_pattern = r'/user/auth'
    endpoint_name = 'user_auth_compute_view'

    def authenticate_user(self):
        """
        We don't need the user to be authenticated
        :return:
        """
        return None

    def compute(self, request, *args, **kwargs):
        request_dict = json.loads(request.body)

        if 'email' not in request_dict and 'username' not in request_dict:
            raise self.BadRequestException("email/username not present")

        if 'password' not in request_dict:
            raise self.BadRequestException("password not present")

        user = authenticate(username=request_dict.get('email') or request_dict.get('username'),
                            password=request_dict['password'])

        if not user:
            raise self.UnauthenticatedException("incorrect credentials")

        if not user.is_active:
            raise self.UnauthorizedException("The user is disabled")

        # Check if the user has an auth token
        try:
            user.auth_token
        except (AttributeError, AuthToken.DoesNotExist):
            AuthToken.create_token_model(user)

        # refresh the token
        user.auth_token.refresh()

        return user_to_dict(user)


class CurrentUserProfileDetailView(DetailView):
    model = UserProfile
    url_pattern = r'/user/me/details$'
    endpoint_name = 'me_profile_detail_view'

    def get_object(self, request, *args, **kwargs):
        return request.user.details


class CurrentUserInitialSampleDocsView(DetailView):
    model = User
    url_pattern = r'/user/me/initial_sample_docs$'
    endpoint_name = 'me_initial_sample_docs_view'

    @classmethod
    def to_dict(cls, item):
        return item

    def get_object(self, request, *args, **kwargs):
        user_documents = Document.objects.filter(owner=request.user, initsample=True)
        return {'samples': [(d.original_name, d.uuid) for d in user_documents]}


class CurrentUserCollaboratorsListView(ListView):
    model = User
    url_pattern = r'/user/me/collaborators$'
    endpoint_name = 'me_collaborators_list_view'

    @classmethod
    def to_dict(cls, item):
        return item

    def get_list(self, request, *args, **kwargs):
        try:
            email_suggestions = self.user.collaborator_aggregate.get_suggestions()
        except CollaboratorList.DoesNotExist:
            collaborator_list = CollaboratorList.create(self.user)
            email_suggestions = collaborator_list.get_suggestions()

        # Extract all emails
        all_emails = set([item['email'] for item in email_suggestions])

        # Get suggested users
        users = User.objects.filter(email__in=all_emails)
        users_emails = set([u.email for u in users])

        # Check the emails that were not found in external invites
        external_emails = all_emails - users_emails
        external_invites = ExternalInvite.objects.filter(inviter=self.user, email__in=external_emails).order_by('email').distinct('email')

        # dictify everything
        suggestion_dicts = [user_to_dict(u) for u in users] + [ei.to_user_dict() for ei in external_invites]

        return suggestion_dicts


class CurrentUserActiveSubscriptionDetailView(DetailView):
    model = User
    url_pattern = r'/user/me/subscription$'
    endpoint_name = 'me_subscription_detail_view'

    def get_object(self, request, *args, **kwargs):
        return request.user

    @classmethod
    def to_dict(cls, model):
        current_subscription = PurchasedSubscription.get_first_current_subscription(model)

        return_dict = {'current_subscription': None}

        if current_subscription:
            return_dict['current_subscription'] = current_subscription.to_dict()
            return_dict['current_subscription']['is_trial'] = (
                not model.is_superuser and TrialSubscription.includes(current_subscription.get_subscription())
            )

        return return_dict


class CurrentUserSubscriptionsListView(ListView):
    model = PurchasedSubscription
    url_pattern = r'/user/me/subscriptions$'
    endpoint_name = 'me_subscriptions_list_view'

    def get_list(self, request, *args, **kwargs):
        return PurchasedSubscription.get_current_subscriptions(self.user)

    @classmethod
    def to_dict(cls, model):
        return_dict = model.to_dict()
        return_dict['is_trial'] = (
            not model.buyer.is_superuser
            and TrialSubscription.includes(model.get_subscription())
        )

        return return_dict


class OnlineLearnersListView(ListView):
    model = User
    url_pattern = r'/user/me/learners$'
    endpoint_name = 'me_learners_list_view'

    def get_list(self, request, *args, **kwargs):
        from ml.facade import LearnerFacade

        learners = LearnerFacade.get_all(self.user, preload=False)
        return learners


class UserSettingsDetailView(DetailView, PutDetailModelMixin):
    """
    PUT request should provide a dictionary of settings to be changed:
      {"setting_A": True, "setting_B": "awesome"}
    """
    model = UserProfile
    url_pattern = r'/user/me/settings/?$'
    endpoint_name = 'me_settings_detail_view'

    def get_object(self, request, *args, **kwargs):
        return request.user.details

    @classmethod
    def to_dict(cls, model):
        return model.settings or {}

    def save_model(self, model, data, request, *args, **kwargs):
        model.update_settings(data)
        return model


class UserRLTEFlagsDetailView(DetailView, PutDetailModelMixin):
    """
    PUT request should provide a dictionary of RLTE flags to be changed:
      {"rlte_flag_A": True, "rlte_flag_B": False}
    """
    model = UserProfile
    url_pattern = r'/user/me/rlte_flags/?$'
    endpoint_name = 'me_rlte_flags_detail_view'

    def get_object(self, request, *args, **kwargs):
        return request.user.details

    @classmethod
    def to_dict(cls, model):
        return model.rlte_flags

    def save_model(self, model, data, request, *args, **kwargs):
        model.update_rlte_flags(data)
        return model


class UserSpotExperimentsStatusView(StatusView):
    url_pattern = r'/user/me/spot/experiments/?$'
    endpoint_name = 'me_spot_experiments_status_view'

    def status(self, request, *args, **kwargs):
        user_profile = request.user.details
        return user_profile.spot_experiments


class UserSpotSuggestionsStatusView(StatusView):
    url_pattern = r'/user/me/spot/suggestions/?$'
    endpoint_name = 'me_spot_suggestions_status_view'

    def status(self, request, *args, **kwargs):
        user_profile = request.user.details
        url = os.path.join(config.SPOT_API_URL, 'publish', 'suggestions') + '/'
        headers = {'X-Access-Token': user_profile.spot_access_token}
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            raise self.UnauthenticatedException(
                'Could not access Spot API due to failed authentication. '
                'Make sure to authorize your account in Spot.'
            )
        if response.status_code == 200:
            return response.json()
        raise self.ServiceUnavailableException(
            'Could not connect to Spot API. Please try again later...'
        )


class UserAddSpotExperimentComputeView(ComputeView):
    url_pattern = r'/user/me/spot/experiments/add/?$'
    endpoint_name = 'me_add_spot_experiment_compute_view'

    def compute(self, request, *args, **kwargs):
        user_profile = request.user.details
        data = json.loads(request.body)
        uuid = data.get('uuid')
        if uuid is None:
            raise self.BadRequestException('No experiment UUID specified!')
        # Actual names of dogbone tags don't make sense in Spot,
        # so simply use the username of the requesting user
        tag = request.user.username
        url = (os.path.join(config.SPOT_API_URL, 'publish', uuid) + '/' +
               '?' + urllib.urlencode({'tag': tag}))
        headers = {'X-Access-Token': user_profile.spot_access_token}
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            raise self.UnauthenticatedException(
                'Could not access Spot API due to failed authentication. '
                'Make sure to authorize your account in Spot.'
            )
        if response.status_code == 404:
            raise self.NotFoundException('Experiment does not exist!')
        if response.status_code == 200:
            metadata = response.json()
            del metadata['uuid']  # redundant field for metadata
            # Fetch and save the current number of samples used for training
            # the corresponding online learner so far
            online_learner_dict = \
                metadata.pop('online_learners', {}).get(tag, {})
            metadata['samples'] = online_learner_dict.get('samples', 0)
            user_profile.set_spot_experiment(uuid, metadata)
            metadata['uuid'] = uuid  # necessary field for response
            return metadata
        raise self.ServiceUnavailableException(
            'Could not connect to Spot API. Please try again later...'
        )


class UserRemoveSpotExperimentComputeView(ComputeView):
    url_pattern = r'/user/me/spot/experiments/remove/?$'
    endpoint_name = 'me_remove_spot_experiment_compute_view'

    def compute(self, request, *args, **kwargs):
        user_profile = request.user.details
        data = json.loads(request.body)
        uuid = data.get('uuid')
        if uuid is None:
            raise self.BadRequestException('No experiment UUID specified!')
        metadata = user_profile.pop_spot_experiment(uuid)
        if metadata is None:
            raise self.NotFoundException('Experiment does not exist!')
        metadata['uuid'] = uuid
        return metadata


class UserResetSpotExperimentComputeView(ComputeView):
    url_pattern = r'/user/me/spot/experiments/reset/?$'
    endpoint_name = 'me_reset_spot_experiment_compute_view'

    def compute(self, request, *args, **kwargs):
        user_profile = request.user.details
        data = json.loads(request.body)
        uuid = data.get('uuid')
        if uuid is None:
            raise self.BadRequestException('No experiment UUID specified!')
        metadata = user_profile.get_spot_experiment(uuid)
        if metadata is None:
            raise self.NotFoundException('Experiment does not exist!')
        # Actual names of dogbone tags don't make sense in Spot,
        # so simply use the username of the requesting user
        tag = request.user.username
        url = os.path.join(config.SPOT_API_URL, 'publish', uuid, 'reset') + '/'
        data = {'tag': tag}
        headers = {'X-Access-Token': user_profile.spot_access_token}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 403:
            raise self.UnauthenticatedException(
                'Could not access Spot API due to failed authentication. '
                'Make sure to authorize your account in Spot.'
            )
        if response.status_code == 404:
            user_profile.pop_spot_experiment(uuid)
            raise self.NotFoundException('Experiment does not exist anymore! '
                                         'It will be deleted from your list.')
        if response.status_code == 200:
            metadata['samples'] = 0
            user_profile.set_spot_experiment(uuid, metadata)
            return metadata
        raise self.ServiceUnavailableException(
            'Could not connect to Spot API. Please try again later...'
        )


class UserActualCollaboratorsStatusView(StatusView):
    """
    Returns usernames from the current user's collaborator list,
    thus unlike /user/me/collaborators this endpoint is more lightweight
    and also it does not take into account any pending external invites.
    Should be used inside the search bar for filtering by comments of a
    specific author.
    """

    url_pattern = r'/user/me/actual_collaborators/?$'
    endpoint_name = 'me_actual_collaborators_status_view'

    def status(self, request, *args, **kwargs):
        collaborator_list, _ = CollaboratorList.objects.get_or_create(user=self.user)
        emails = [entry['email'] for entry in collaborator_list.get_suggestions()]
        # Also allow filtering by the owner's comments
        emails.append(self.user.email)
        users = User.objects.filter(email__in=emails).order_by('username')
        usernames = [user.username for user in users]
        return usernames


class UserProjectsListView(ListView):
    """
    Lists all documents the user has access to (either as the owner or
    as a collaborator). Also includes advanced search and filtering.
    """

    url_pattern = r'/user/me/projects/?$'
    endpoint_name = 'me_projects_list_view'

    _cached_object_count = None

    DEFAULT_RESULTS_PER_PAGE = 10

    FALSE_BOOLS = ('0', 'false', 'False')
    TRUE_BOOLS = ('1', 'true', 'True')
    BOOLS = FALSE_BOOLS + TRUE_BOOLS

    @staticmethod
    def to_user_dict(user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or None,
            'last_name': user.last_name or None,
            'avatar': user.details.get_avatar()
        }

    @classmethod
    def to_dict(cls, model):
        # The model is either a batch or a document

        model_dict = {
            'owner': cls.to_user_dict(model.owner),
            'created': model.created.isoformat()
        }

        model_meta = {}

        model_type = model.__class__.__name__.lower()

        if model_type == 'batch':
            model_meta['batch_id'] = model.id
            model_meta['analyzed'] = model.is_analyzed

            if model.is_trivial:
                model = model.get_documents_queryset().last()
                model_type = 'document'

            else:
                model_dict['documents_count'] = model.documents_count

                model_meta['batch_name'] = model.name
                model_meta['created'] = model.created.isoformat()

        if model_type == 'document':
            model_dict['documents_count'] = 1

            model_meta['uuid'] = model.uuid
            model_meta['status'] = int(model.is_ready)
            model_meta['failed'] = model.failed
            model_meta['title'] = model.title
            model_meta['agreement_type'] = model.get_agreement_type()
            model_meta['processing_begin_timestamp'] = (
                model.processing_begin_timestamp.isoformat()
                if model.processing_begin_timestamp else
                None
            )
            model_meta['parties'] = model.get_parties_full()

        model_dict['report_url'] = model.get_report_url()

        model_dict['meta'] = model_meta

        return model_dict

    def get_object_count(self):
        """
        Determine total number of objects in this list view.
        Returns a cached object count, no queries are made.
        """
        return self._cached_object_count

    def get_page_count(self):
        """ Determine total number of pages in this result, given the RPP. """
        rpp = self.get_rpp()
        object_count = self.get_object_count()
        return self._compute_page_count(object_count, rpp)

    def search(self):
        return self._get_request_params(self.request)

    def meta(self):
        return {'pagination': self.pagination(),
                'search': self.search()}

    def wrap_result(self, result):
        return {'objects': result,
                'meta': self.meta()}

    def _get_request_params(self, request):
        owned = request.GET.get('owned')
        if owned and owned in self.BOOLS:
            owned = owned in self.TRUE_BOOLS
        else:
            owned = True  # undefined or invalid value

        invited = request.GET.get('invited')
        if invited and invited in self.BOOLS:
            invited = invited in self.TRUE_BOOLS
        else:
            invited = True  # undefined or invalid value

        query = request.GET.get('q', '')

        changes = request.GET.get('track')
        if changes and changes in self.BOOLS:
            changes = changes in self.TRUE_BOOLS
        else:
            changes = False  # undefined or invalid value

        comments = request.GET.getlist('comments')
        learners = request.GET.getlist('learners')
        keywords = request.GET.getlist('keywords')

        return {'owned': owned,
                'invited': invited,
                'query': query,
                'changes': changes,
                'comments': comments,
                'learners': learners,
                'keywords': keywords}

    def _filter_documents(self, request):
        request_params = self._get_request_params(request)

        documents = Document.get_aggregated_documents(self.user)
        documents = documents.select_related('owner', 'batch__owner')

        if not request_params['owned']:
            documents = documents.exclude(owner=self.user)
        if not request_params['invited']:
            documents = documents.filter(owner=self.user)

        query = request_params['query']
        if query:
            documents = documents.filter(title__icontains=query)

        changes = request_params['changes']
        comments = request_params['comments']
        learners = request_params['learners']
        keywords = request_params['keywords']

        # Deeper filtering needed (cannot be handled by the QuerySet API)
        if changes or comments or learners or keywords:
            fields = []
            if comments:
                fields.append('comments')
            if learners or keywords:
                fields.append('annotations')

                excluded = [SentenceAnnotations.MANUAL_TAG_TYPE,
                            SentenceAnnotations.ANNOTATION_TAG_TYPE]
                if not learners:
                    excluded.append(SentenceAnnotations.SUGGESTED_TAG_TYPE)
                if not keywords:
                    excluded.append(SentenceAnnotations.KEYWORD_TAG_TYPE)

            filtered_documents = []

            for document in documents:
                match = {'changes': not changes,
                         'comments': not comments,
                         'learners': not learners,
                         'keywords': not keywords}

                sentences = document.get_sentences_queryset().only(*fields)

                for sentence in sentences:
                    if changes:
                        if not match['changes']:
                            if not sentence.accepted:
                                match['changes'] = True

                    if comments:
                        if not match['comments']:
                            # Authors of imported comments are just placeholders
                            # (the document's owner is set as an author)
                            authors = frozenset(
                                comment['author'] for comment in
                                sentence.get_comments(include_imported=False)
                            )
                            if authors.intersection(comments):
                                match['comments'] = True

                    if learners or keywords:
                        if not match['learners'] or not match['keywords']:
                            tags = sentence.get_tags_by_type(excluded=excluded)

                            if not match['learners']:
                                learner_tags = tags[SentenceAnnotations.SUGGESTED_TAG_TYPE]
                                if learner_tags.intersection(learners):
                                    match['learners'] = True

                            if not match['keywords']:
                                keyword_tags = tags[SentenceAnnotations.KEYWORD_TAG_TYPE]
                                if keyword_tags.intersection(keywords):
                                    match['keywords'] = True

                ok = all(match.values())
                if ok:
                    filtered_documents.append(document)

            documents = filtered_documents

        return documents

    def get_queryset(self, request):
        documents = self._filter_documents(request)

        # Group owned documents by corresponding batches
        # (a batch is considered as matched if at least one
        # of its documents was matched by the given query)
        owned_batches_ids = set()

        # Separate invited documents from owned batches
        invited_documents_ids = set()

        for document in documents:
            if document.owner == self.user:
                batch = document.batch
                owned_batches_ids.add(batch.id)
            else:
                invited_documents_ids.add(document.id)

        return list(owned_batches_ids), list(invited_documents_ids)

    @staticmethod
    def _merge(A, B, key=None, reverse=False):
        """
        Merges two sorted sequences A and B into another sorted sequence C.
        """

        if key is None:
            key = lambda item: item  # identity function by default

        if reverse:
            lt = lambda a, b: key(a) > key(b)
        else:
            lt = lambda a, b: key(a) < key(b)

        C = []

        i, m = 0, len(A)
        j, n = 0, len(B)

        while i < m and j < n:
            if lt(A[i], B[j]):
                C.append(A[i])
                i += 1
            else:
                C.append(B[j])
                j += 1

        while i < m:
            C.append(A[i])
            i += 1

        while j < n:
            C.append(B[j])
            j += 1

        return C

    def get_list(self, request, *args, **kwargs):
        # Cache the obtained batches along with the corresponding
        # set of filters after the very first successful request.

        # We store batches, because it allows us to have the most fresh
        # stats after each request despite caching (Batch.to_dict performs that
        # gathering for each contained document).

        cache_key = 'user:projects:%d' % self.user.id

        data = cache.get(cache_key)

        filters = self.search()

        if data is None or data['filters'] != filters:
            owned_batches_ids, invited_documents_ids = self.get_queryset(request)

            data = {
                'filters': filters,
                'owned_batches_ids': owned_batches_ids,
                'invited_documents_ids': invited_documents_ids,
            }

            cache.set(cache_key, data, timeout=300)

        else:
            owned_batches_ids = data['owned_batches_ids']
            invited_documents_ids = data['invited_documents_ids']

        owned_batches = Batch.objects.filter(
            id__in=owned_batches_ids
        ).select_related('owner__details').order_by('-created')

        invited_documents = Document.objects.filter(
            id__in=invited_documents_ids
        ).select_related('owner__details').order_by('-created')

        # Owned batches and invited documents are already sorted,
        # so simply merge them into another sorted list
        models = self._merge(owned_batches, invited_documents,
                             key=lambda model: model.created,
                             reverse=True)

        self._cached_object_count = len(models)

        return models[self.get_slice()]

    def get(self, request, *args, **kwargs):
        return map(self.to_dict, self.get_list(request, *args, **kwargs))
