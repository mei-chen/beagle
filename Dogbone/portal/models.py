from datetime import date
import jsonfield
import logging

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.forms import ValidationError
from django.db.utils import ProgrammingError
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete, pre_save

from core.models import ExternalInvite, Document
from marketing.models import Coupon, PurchasedSubscription, PaymentRecord
from marketing.signals import subscription_extended, subscription_expired, subscription_purchased
from marketing.exceptions import InvalidSubscriptionException
from marketing.subscriptions import Subscription
from integrations.s3 import ssl_s3url
from integrations.tasks import send_slack_message, log_intercom_custom_event, update_intercom_document_count
from statistics.tasks import log_statistic_event
from statistics.models import EVENT_TYPES
from keywords.signals import keyword_deleted, keyword_deactivated, keyword_created, keyword_activated
from keywords.models import SearchKeyword
from authentication.models import AuthToken

from .tools import decrypt_str
from .tasks import (hubspot_update_contact_properties,
                    add_keyword_to_cache, remove_keyword_from_cache)


RLTE_FLAGS = [
    'terminations',
    'liabilities',
    'responsibilities',
    'external_references'
]


def generate_default_rlte_flags():
    # Everything is enabled by default
    return {flag: True for flag in RLTE_FLAGS}


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='details', on_delete=models.CASCADE)
    job_title = models.TextField(default='', null=True, blank=True)
    company = models.TextField(default='', null=True, blank=True)
    phone = models.TextField(default='', max_length=25, null=True, blank=True)
    document_upload_count = models.IntegerField(null=True)  # initialize to null

    # Handle in APIs if this is NULL and set it to '/static/img/mug.png'
    avatar = models.ImageField(upload_to="profile_photo/%Y/%m/%d/", blank=True, null=True)
    avatar_s3 = models.CharField('S3 Avatar address', blank=True, null=True, max_length=255,
                                 help_text='Format: bucket:filename')

    # Caches
    tags_cache = jsonfield.JSONField('Tags Cache', null=True, default=None, blank=True)
    keywords_cache = jsonfield.JSONField('Keywords Cache', null=True, default=None, blank=True)

    # Onboarding details
    initial_tour = models.DateTimeField('Initial Tour', default=None, null=True)

    # Settings
    settings = jsonfield.JSONField('User Settings', null=True, default=None, blank=True)

    # RLTE flags
    rlte_flags = jsonfield.JSONField('User RLTE Flags', default=generate_default_rlte_flags)

    # Spot-related data
    spot = jsonfield.JSONField('Spot', null=True, default=None, blank=True)

    # Kibble-related data
    kibble = jsonfield.JSONField('Kibble', null=True, default=None, blank=True)

    @classmethod
    def get_or_create_profile(cls, user):
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            logging.info('UserProfile created for %s', user)
        return profile

    @property
    def tags(self):
        """
        Properly unwrap the tags json list
        """
        if not self.tags_cache:
            return []
        return self.tags_cache['tags']

    @property
    def keywords(self):
        """
        Properly unwrap the keywords json list
        """
        if not self.keywords_cache:
            return []
        return self.keywords_cache['keywords']

    def get_document_upload_count(self):
        if self.document_upload_count is None:
            self.document_upload_count = len(Document.objects.filter(owner=self.user))
            self.save()

        return self.document_upload_count

    def inc_document_upload_count(self, count=1):
        if self.document_upload_count is None:
            self.get_document_upload_count()
        else:
            self.document_upload_count += count
        self.save()

    def add_tag(self, tag):
        """
        Add a tag to the `tags_cache` json list
        """
        if not self.tags_cache:
            self.tags_cache = {'tags': [tag]}
        elif tag not in self.tags:
            self.tags_cache['tags'].append(tag)
        self.save()

    def add_keyword(self, keyword):
        """
        Add a tag to the `keywords_cache` json list
        """
        if not self.keywords_cache:
            self.keywords_cache = {'keywords': [keyword]}
        elif keyword not in self.keywords:
            self.keywords_cache['keywords'].append(keyword)

        self.save()

    def remove_keyword(self, keyword):
        """
        Remove a tag from the `keywords_cache` json list
        """
        if keyword not in self.keywords:
            return

        self.keywords_cache['keywords'].remove(keyword)

        self.save()

    def update_settings(self, settings_dict):
        """
        :settings_dict should be a dictionary containing the settings that
        need to be changed (similar to setState in React)
        E.g.:
          - settings before: {'a': True, 'b': False, 'c': False}
          - user.putSettings({'a': False, 'b': False})
          - settings after: {'a': False, 'b': False, 'c': False}
        """
        if not (settings_dict and isinstance(settings_dict, dict)):
            return

        if self.settings is None:
            self.settings = {}
        self.settings.update(settings_dict)
        self.save()

    def update_rlte_flags(self, rlte_flags_dict):
        """
        Works the same way as `update_settings`, but only updates RLTE flags
        instead. Also validates :rlte_flags_dict by discarding invalid flags.
        """
        if not (rlte_flags_dict and isinstance(rlte_flags_dict, dict)):
            return

        rlte_flags_dict = {
            key: value for key, value in rlte_flags_dict.items()
            if key in RLTE_FLAGS  # discard invalid entries
        }

        self.rlte_flags.update(rlte_flags_dict)
        self.save()

    def get_avatar(self):
        return '/static/img/mug.png' if not self.avatar_s3 else ssl_s3url(*self.avatar_s3.split(':'))

    def to_dict(self):
        return {
            'job_title': self.job_title,
            'company': self.company,
            'phone': self.phone,
            'avatar': self.get_avatar(),
            'document_upload_count': self.document_upload_count,
            'tags': self.tags,
            'keywords': self.keywords,
            'settings': self.settings,
        }

    def __str__(self):
        return 'Details for %s %s (%s)' % (self.user.first_name, self.user.last_name, self.user.email)

    class Meta:
        verbose_name = 'User Details'
        verbose_name_plural = 'Users Details'

    # Spot-related stuff

    @property
    def spot_experiments(self):
        return (self.spot or {}).get('experiments', {})

    def get_spot_experiment(self, uuid):
        return self.spot_experiments.get(uuid)

    def pop_spot_experiment(self, uuid):
        metadata = self.spot_experiments.pop(uuid, None)
        self.save()
        return metadata

    def set_spot_experiment(self, uuid, metadata):
        if not self.spot:
            self.spot = {}
        if 'experiments' not in self.spot:
            self.spot['experiments'] = {}
        self.spot['experiments'][uuid] = metadata
        self.save()

    def get_spot_access_token(self):
        return (self.spot or {}).get('access_token')

    def set_spot_access_token(self, access_token):
        if not self.spot:
            self.spot = {}
        self.spot['access_token'] = access_token
        self.save()

    spot_access_token = property(get_spot_access_token, set_spot_access_token)

    # Kibble-related stuff

    def get_kibble_access_token(self):
        return (self.kibble or {}).get('access_token')

    def set_kibble_access_token(self, access_token):
        if not self.kibble:
            self.kibble = {}
        self.kibble['access_token'] = access_token
        self.save()

    kibble_access_token = property(get_kibble_access_token, set_kibble_access_token)


@receiver(pre_save, sender=User)
def lowercase_user_email(sender, **kwargs):
    """
    Make the `email` field lowercase every time, before the user is saved
    """
    if kwargs['instance'].email:
        kwargs['instance'].email = kwargs['instance'].email.lower()

@receiver(pre_save, sender=User)
def validate_unique_email(sender, **kwargs):
    email = kwargs['instance'].email
    user_id = kwargs['instance'].pk
    if not email:
        return

    if sender.objects.filter(email__iexact=email).exclude(pk=user_id).count():
        raise ValidationError("email needs to be unique")

# Create a UserProfile each time a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    if kwargs['created']:
        UserProfile.get_or_create_profile(kwargs['instance'])

# Create an Auth Token for the user
@receiver(post_save, sender=User)
def create_auth_token(sender, **kwargs):
    if kwargs["created"]:
        user = kwargs["instance"]
        AuthToken.create_token_model(user)

# Trigger adding initial sample docs to new User accounts
@receiver(post_save, sender=User)
def add_init_samples(sender, **kwargs):
    from core.tasks import initialize_sample_docs
    if kwargs['created']:
        initialize_sample_docs.delay(kwargs['instance'].id)

# Trigger adding pre-trained learners to a new User
@receiver(post_save, sender=User)
def add_pretrained(sender, **kwargs):
    from core.tasks import install_pretrained
    if kwargs['created']:
        install_pretrained.delay(kwargs['instance'].id)

# Delete a UserProfile each time a User is deleted
@receiver(pre_delete, sender=User)
def delete_user_profile(sender, **kwargs):
    try:
        kwargs['instance'].details.delete()
    except UserProfile.DoesNotExist:
        pass

@receiver(models.signals.post_save, sender=Document)
def increment_document_upload_count(sender, **kwargs):
    if kwargs['created']:
        logging.info("increment_document_upload_count for user=%s" % kwargs['instance'].owner)
        kwargs['instance'].owner.details.inc_document_upload_count()


@receiver(models.signals.post_save, sender=Document)
def log_intercom_document_upload(sender, **kwargs):
    if kwargs['created']:

        # Log a document upload event in Intercom
        upload_metadata = {
            'Title': kwargs['instance'].title,
            'Source': kwargs['instance'].upload_source
        }

        log_intercom_custom_event.delay(email=kwargs['instance'].owner.email,
                                        event_name=EVENT_TYPES['document_uploaded'],
                                        metadata=upload_metadata)


@receiver(models.signals.post_save, sender=Document)
def log_statistics_document_upload(sender, **kwargs):
    if kwargs['created']:

        # Log a document upload event in Statistics
        upload_metadata = {
            'Title': kwargs['instance'].title,
            'Source': kwargs['instance'].upload_source
        }

        log_statistic_event.delay(event_name='document_uploaded',
                                  event_user_id=kwargs['instance'].owner.id,
                                  event_data=upload_metadata)


@receiver(models.signals.post_save, sender=Document)
def update_intercom_document_uploaded_count(sender, **kwargs):
    if kwargs['created']:
        # Update Intercom document upload count
        from django.conf import settings
        if not settings.DEBUG:
            update_intercom_document_count.delay(email=kwargs['instance'].owner.email)


@receiver(models.signals.post_save, sender=Document)
def update_hubspot_document_uploaded_count(sender, **kwargs):
    if kwargs['created']:
        # Report new upload count to hubspot
        hs_data = [{
            "property": "documents_uploaded",
            "value": kwargs['instance'].owner.details.get_document_upload_count()
        }]
        hubspot_update_contact_properties.delay(email=kwargs['instance'].owner.email, data=hs_data)


@receiver(models.signals.post_save, sender=User)
def create_collaboration_invites(sender, instance, created, **kwargs):
    """
    Create CollaborationInvite for every ExternalInvite
    """
    if created:
        try:

            external_invites = ExternalInvite.pending_objects.filter(email=instance.email)
            documents_invited_to = []

            for ext_invite in external_invites:
                ext_invite.create_collaboration_invite(instance)
                documents_invited_to.append(ext_invite.document)

            documents_invited_to = list(set(documents_invited_to))

            from core.tasks import parse_comments_on_external_invite_delete, bounce_delayed_notifications
            document_ids = [d.id for d in documents_invited_to]
            parse_comments_on_external_invite_delete.delay(document_ids, instance.id)
            bounce_delayed_notifications.delay(email=instance.email)
        except ProgrammingError:
            logging.error("ExternalInvites table does not exist yet")


class WrongAnalysisFlag(models.Model):
    # User inserted
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doc = models.ForeignKey(Document, on_delete=models.CASCADE)
    comments = models.TextField(default='', blank=True, null=True)

    # Resolution
    resolved = models.BooleanField('Resolved?', default=False)
    resolution_comments = models.TextField(default='', blank=True, null=True)

    def __str__(self):
        return 'Flag: %s%s (%s)' % (self.doc.original_name[:25],
                                    '...' if len(self.doc.original_name) > 25 else '',
                                    self.user.email)

    class Meta:
        verbose_name = 'Wrong Analysis Flag'
        verbose_name_plural = 'Wrong Analysis Flags'


########################################################################################
#
#   Payments
#
########################################################################################


from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received


def handle_successful_transaction(sender, **kwargs):
    logging.info('Arrived at handle_successful_transaction')
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        logging.info('handle_successful_transaction: Payment status completed')
        # TODO: Send a CRM notification

        uid, email, coupon_code = decrypt_str(ipn_obj.custom).split('$')
        logging.info('handle_successful_transaction: uid=%s, email=%s, coupon_code=%s' % (uid, email, coupon_code))

        # Init the coupon object
        coupon = None

        if coupon_code:
            coupon = Coupon.get_by_code(coupon_code)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logging.error('Received payment confirmation for an invalid user=%s' % email)
            return

        try:
            subscription = Subscription.get_by_uid(uid)
        except InvalidSubscriptionException:
            logging.error('Received payment confirmation for an invalid subscription uid=%s' % uid)
            return

        send_slack_message('User %s purchased a %s subscription' % (user, str(subscription)),
                                    '#sales_and_marketing')

        if coupon:
            purchased_subscription = coupon.create_subscription(user, persist=True)
            coupon.add_user_to_group(user)
        else:
            purchased_subscription = PurchasedSubscription.purchase_subscription(user, subscription, coupon)

        PaymentRecord.create_record(user, purchased_subscription, ipn_obj.amount, ipn_obj.currency, ipn_obj.invoice)
    else:
        pass

valid_ipn_received.connect(handle_successful_transaction)


def handle_failed_transaction(sender, **kwargs):
    logging.error('Arrived handle_failed_transaction, please check payment')
    # TODO: Send a CRM notification
    # ipn_obj = sender

invalid_ipn_received.connect(handle_failed_transaction)


def handle_payment_was_flagged(sender, **kwargs):
    """
    Log in the transaction flag information
    """
    ipn_obj = sender
    try:
        logging.error("PayPal transaction was flagged with: flag=%s" % ipn_obj.flag_info)
    except Exception as e:
        logging.error('Exception in handle_payment_was_flagged exc=%s', str(e))


@receiver(subscription_purchased, sender=PurchasedSubscription)
def hubspot_notify_subscription_purchased(sender, user, purchased_subscription, **kwargs):
    from .tasks import hubspot_submit_form
    from django.conf import settings

    coupon_code = purchased_subscription.coupon_used.code if purchased_subscription.coupon_used else None
    if not settings.DEBUG:

        hubspot_submit_form.delay(settings.HUBSPOT_SUBSCRIPTION_STARTED_FORM_GUID,
                              page_name='PurchaseSubscriptionForm',
                              url=None, ip=None, hutk=None,
                              data={
                                  'email': user.email,
                                  'username': user.username,
                                  'lifecyclestage': 'lead',
                                  'hs_lead_status': 'QUALIFIED',
                                  'subscription_type': purchased_subscription.get_subscription().uid,
                                  'subscription_price': purchased_subscription.purchase_price,
                                  'coupon_code': coupon_code,
                              })


@receiver(subscription_extended, sender=PurchasedSubscription)
def hubspot_notify_subscription_extended(sender, user, purchased_subscription, **kwargs):
    from .tasks import hubspot_submit_form
    from django.conf import settings
    if not settings.DEBUG:

        hubspot_submit_form.delay(settings.HUBSPOT_SUBSCRIPTION_STARTED_FORM_GUID,
                              page_name='ExtendSubscriptionForm',
                              url=None, ip=None, hutk=None,
                              data={
                                  'email': user.email,
                                  'username': user.username,
                                  'lifecyclestage': 'lead',
                                  'hs_lead_status': 'QUALIFIED',
                                  'subscription_type': purchased_subscription.get_subscription().uid,
                              })


@receiver(subscription_expired, sender=PurchasedSubscription)
def hubspot_notify_subscription_expired(sender, user, purchased_subscription, **kwargs):
    from .tasks import hubspot_submit_form
    from django.conf import settings

    if not settings.DEBUG:
        hubspot_submit_form.delay(settings.HUBSPOT_SUBSCRIPTION_STARTED_FORM_GUID,
                              page_name='ExpireSubscriptionForm',
                              url=None, ip=None, hutk=None,
                              data={
                                  'email': user.email,
                                  'username': user.username,
                                  'lifecyclestage': 'lead',
                                  'hs_lead_status': 'QUALIFIED',
                                  'subscription_type': purchased_subscription.get_subscription().uid,
                              })


@receiver(keyword_created, sender=SearchKeyword)
@receiver(keyword_activated, sender=SearchKeyword)
def run_add_keyword_to_cache_on_create(sender, user, keyword, **kwargs):
    if keyword.active:
        add_keyword_to_cache.delay(keyword.pk)


@receiver(keyword_deactivated, sender=SearchKeyword)
@receiver(keyword_deleted, sender=SearchKeyword)
def run_remove_keyword_from_cache(sender, user, keyword, **kwargs):
    remove_keyword_from_cache.delay(user.pk, keyword.keyword)

########################################################################################
#
#   PDF Upload monitoring
#
########################################################################################

class PDFUploadMonitor(models.Model):
    docs = models.IntegerField(default=0)
    pages = models.IntegerField(default=0)
    docs_ocred = models.IntegerField(default=0)
    pages_ocred = models.IntegerField(default=0)

    startdate = models.DateField(default=timezone.now)

    def add_doc(self, pages, ocr=False):
        if not (date.today().month == self.startdate.month and
                date.today().year == self.startdate.year):
            # Need to initialize a new month statistics
            stat = PDFUploadMonitor()
        else:
            stat = self

        # Add the counts and save
        if ocr:
            stat.docs_ocred += 1
            stat.pages_ocred += pages
        else:
            stat.docs += 1
            stat.pages += pages
        stat.save()

    def __str__(self):
        return '%s-%s: %dpg / %dd (%dpg / %dd OCR)' % (
                    str(self.startdate.month), str(self.startdate.year),
                    self.pages, self.docs,
                    self.pages_ocred, self.docs_ocred)

    class Meta:
        verbose_name = 'PDF Upload monitoring'
        verbose_name_plural = 'PDF Upload monitoring'
        get_latest_by = 'startdate'
