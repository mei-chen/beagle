import uuid
import json
import urllib
import logging
from base64 import b64decode

from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.conf import settings

from beagle_simpleapi.endpoint import DetailView, ActionView
from beagle_simpleapi.mixin import PostListModelMixin
from api_v1.decorators import internal_or_exception
from core.tools import user_to_dict
from core.tasks import send_auto_account_created_notification,\
    send_unsupported_file_type_notification, send_help_notification, \
    send_attachments_not_found_notification
from integrations.s3 import get_s3_bucket_manager
from portal.tasks import hubspot_update_contact_properties, hubspot_get_vid
from portal.tools import random_str
from authentication.models import OneTimeLoginHash
from api_v1.document.endpoints import DocumentUploadComputeView
from marketing.models import PurchasedSubscription, Subscription
from marketing.subscriptions import InvalidSubscriptionException
from utils.django_utils.query import get_user_by_identifier


class InternalUserDetailView(DetailView):
    model = User
    url_pattern = r'/_internal/user/(?P<identifier>[a-zA-Z0-9\-\+_@%\.]+)$'
    endpoint_name = 'internal_user_detail_view'

    @classmethod
    def to_dict(cls, model):
        return user_to_dict(model)

    @method_decorator(internal_or_exception)
    def get(self, request, *args, **kwargs):
        return super(InternalUserDetailView, self).get(request, *args, **kwargs)

    def get_object(self, request, *args, **kwargs):
        try:
            identifier = urllib.unquote(kwargs['identifier'])
        except KeyError:
            raise self.BadRequestException("Please provide a valid identifier")

        user = get_user_by_identifier(identifier)
        if user is None:
            raise self.NotFoundException("This username does not exist")

        return user

    def authenticate_user(self):
        return None


class InternalUserListView(DetailView, PostListModelMixin):
    model = User
    url_pattern = r'/_internal/user$'
    endpoint_name = 'internal_user_list_view'

    @classmethod
    def to_dict(cls, model):
        return user_to_dict(model)

    @method_decorator(internal_or_exception)
    def get(self, request, *args, **kwargs):
        return super(InternalUserListView, self).get(request, *args, **kwargs)

    @method_decorator(internal_or_exception)
    def post(self, request, *args, **kwargs):
        self.send_auto_create = False
        if request.GET.get('send_auto_create'):
            self.send_auto_create = True

        return super(InternalUserListView, self).post(request, *args, **kwargs)

    def authenticate_user(self):
        return None

    def save_model(self, model, data, request, *args, **kwargs):
        properties = []

        if 'password' not in data or not data['password']:
            data['password'] = random_str(8)

        model.set_password(data['password'])

        if 'email' not in data or not data['email']:
            raise self.BadRequestException("Provide an email")

        model.email = data['email']

        if 'username' in data and data['username']:
            model.username = data['username']
        else:
            model.username = data['email']

        if 'first_name' in data and data['first_name']:
            model.first_name = data['first_name']
            properties.append({'property': 'firstname', 'value': data['first_name']})

        if 'last_name' in data and data['last_name']:
            model.last_name = data['last_name']
            properties.append({'property': 'lastname', 'value': data['last_name']})

        model.save()

        if 'phone' in data and data['phone']:
            model.details.phone = data['phone']
            properties.append({'property': 'phone', 'value': data['phone']})

        if 'job_title' in data and data['job_title']:
            model.details.job_title = data['job_title']
            properties.append({'property': 'jobtitle', 'value': data['job_title']})

        if 'company' in data and data['company']:
            model.details.company = data['company']
            properties.append({'property': 'company', 'value': data['company']})

        if 'avatar' in data and data['avatar']:
            data = b64decode(data['avatar'].split(",")[1])
            filename = str(uuid.uuid4()) + '.png'
            s3manager = get_s3_bucket_manager(settings.PROFILE_PICTURE_BUCKET)
            today = now().date()
            s3key = "profile_photo/%s/%s/%s/%s" % (today.year, today.month, today.day, filename)
            s3manager.save_string(s3key, data, acl='public-read')
            model.details.avatar_s3 = '%s:%s' % (settings.PROFILE_PICTURE_BUCKET, s3key)

        # Send update to hubspot if Prod and changes have been made
        if len(properties) > 0 and settings.DEBUG is False:
            hubspot_update_contact_properties.delay(model.email, properties)

        model.details.save()
        
        if hasattr(self, 'send_auto_create') and self.send_auto_create:
            h = OneTimeLoginHash.create(model)
            send_auto_account_created_notification.delay(h.pk)

        return model


class InternalDocumentUploadComputeView(DocumentUploadComputeView):
    url_pattern = r'/_internal/document/upload$'
    endpoint_name = 'internal_document_upload_compute_view'

    @method_decorator(internal_or_exception)
    def post(self, request, *args, **kwargs):
        return super(InternalDocumentUploadComputeView, self).post(request, *args, **kwargs)

    def allow(self):
        return True

    def authenticate_user(self):
        try:
            user = get_user_by_identifier(self.request.GET['from'])

            # Monkey patch the request
            self.request.user = user
            self.user = user

            return user
        except KeyError, User.DoesNotExist:
            raise self.UnauthenticatedException("Please specify an existing user in GET from={{ email }}")


class InternalAddSubscriptionActionView(ActionView):
    model = User
    url_pattern = r'/_internal/user/(?P<identifier>[a-zA-Z0-9\-\+_@%\.]+)' \
                  r'/subscription/(?P<subscription_id>[a-zA-Z0-9\-_@%\.]+)$'
    endpoint_name = 'internal_add_subscription_action_view'

    @method_decorator(internal_or_exception)
    def post(self, request, *args, **kwargs):
        return super(InternalAddSubscriptionActionView, self).post(request, *args, **kwargs)

    @classmethod
    def to_dict(cls, model):
        return model

    def get_object(self, request, *args, **kwargs):
        identifier = urllib.unquote(kwargs['identifier'])
        user = get_user_by_identifier(identifier)

        if user is None:
            raise self.NotFoundException("This username does not exist")

        return user

    def authenticate_user(self):
        return None

    def action(self, request, *args, **kwargs):
        try:
            s = Subscription.get_by_uid(kwargs['subscription_id'])
        except InvalidSubscriptionException:
            raise self.BadRequestException("Invalid subscription")

        ps = PurchasedSubscription.purchase_subscription(self.instance, s)
        return ps.to_dict()


class InternalNotifyUserView(ActionView):
    model = User
    url_pattern = r'/_internal/user/(?P<identifier>[a-zA-Z0-9\-\+_@%\.]+)' \
                  r'/notify/(?P<notification_type>[a-zA-Z0-9\-_@%\.]+)$'
    endpoint_name = 'internal_user_notify_action_view'

    @method_decorator(internal_or_exception)
    def post(self, request, *args, **kwargs):
        return super(InternalNotifyUserView, self).post(request, *args, **kwargs)

    @classmethod
    def to_dict(cls, model):
        return model

    def authenticate_user(self):
        return None

    def get_object(self, request, *args, **kwargs):
        identifier = urllib.unquote(kwargs['identifier'])
        user = get_user_by_identifier(identifier)

        if user is None:
            raise self.NotFoundException("This username does not exist")

        return user

    def action(self, request, *args, **kwargs):
        notification_type = kwargs['notification_type']

        if notification_type == 'unsupported_file_type':
            try:
                data = json.loads(request.body)
                document_title = data['title']
            except (ValueError, KeyError):
                logging.error('Could not decode the document title from the sent payload')
                raise self.BadRequestException('Could not decode the document title from the sent payload')

            send_unsupported_file_type_notification.delay(self.instance.pk, document_title)
        elif notification_type == 'help':
            send_help_notification.delay(self.instance.pk)
        elif notification_type == 'attachments_not_found':
            send_attachments_not_found_notification.delay(self.instance.pk)
        else:
            raise self.BadRequestException("Invalid notification type")

        return {'success': True}
