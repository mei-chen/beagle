import logging

from dogbone.tools import absolutify
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from django.conf import settings

from nlplib.utils import preformat_markers
from portal.settings import UserSettings


class Mailer(object):
    class UnsentEmailException(Exception):
        pass

    @classmethod
    def send(cls, to_email, from_email, subject, template, html_template, args):
        """
        Sends an email

        :param to_email:
        :param from_email:
        :param subject: Title of email
        :param template: The email template from /templates/email
        :param html_template: The email template from /templates/email/html
        :param args: the arguments for rendering the template
        :return:
        """
        context = Context(args)
        rendered_body = get_template(template).render(context)
        rendered_html_body = get_template(html_template).render(context)

        if not isinstance(to_email, list) and not isinstance(to_email, tuple):
            to_email = [to_email]

        try:
            msg = EmailMultiAlternatives(subject, rendered_body, from_email, to_email)
            msg.attach_alternative(rendered_html_body, "text/html")
            msg.send(fail_silently=not settings.DEBUG)
            return True
        except Exception as e:
            logging.error("Failed to send email: %s", str(e))
            return False


class BeagleMailer(Mailer):
    NOREPLY_FROM_EMAIL = 'noreply@beagle.ai'
    SUPPORT_FROM_EMAIL = 'Beagle Support <support@beagle.ai>'
    DEFAULT_FROM_EMAIL = SUPPORT_FROM_EMAIL

    @classmethod
    def address_user(cls, user):
        if user.first_name:
            return user.first_name.capitalize()

        if user.last_name:
            return user.last_name.capitalize()

        if user.username and '@' not in user.username:
            return user.username

        if user.username and '@' in user.username:
            chunks = user.username.split('@')
            first_chunk = chunks[0]

            if first_chunk.lower() not in ['contact', 'office', 'info', 'hello', 'sales']:
                return first_chunk.lower()

        return 'Sir/Madam'

    @classmethod
    def send_external_invite(cls, external_invite, signup_url):
        subject = "%s invited you to collaborate on Beagle.ai" % cls.address_user(external_invite.inviter)
        template = 'email/external_invite.html'
        html_template = 'email/html/external_invite.html'

        user_settings = UserSettings(external_invite.inviter)
        sentence = external_invite.sentence
        if user_settings.get_setting('include_clause_in_outcoming_mention_emails') and sentence:
            # Convert text with internal markers to some preformatted text
            sent_text = preformat_markers(sentence.text)
            # Add some large limit to avoid abuse
            sent_text = sent_text[:5000]
        else:
            sent_text = None

        return cls.send(to_email=external_invite.email,
                        from_email='Beagle.ai Collaboration Invitation <noreply@beagle.ai>',
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'firstname': cls.address_user(external_invite.inviter),
                              'document_title': external_invite.document.title,
                              'follow_url': signup_url,
                              'sentence_text': sent_text})

    @classmethod
    def send_collaboration_invite(cls, collaboration_invite, follow_url):
        subject = "%s invited you to collaborate on Beagle.ai" % cls.address_user(collaboration_invite.inviter)
        template = 'email/collaboration_invite.html'
        html_template = 'email/html/collaboration_invite.html'

        user_settings = UserSettings(collaboration_invite.inviter)
        sentence = collaboration_invite.sentence
        if user_settings.get_setting('include_clause_in_outcoming_mention_emails') and sentence:
            # Convert text with internal markers to some preformatted text
            sent_text = preformat_markers(sentence.text)
            # Add some large limit to avoid abuse
            sent_text = sent_text[:5000]
        else:
            sent_text = None

        return cls.send(to_email=collaboration_invite.invitee.email,
                        from_email='Beagle.ai Collaboration Invitation <noreply@beagle.ai>',
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'inviter_name': cls.address_user(collaboration_invite.inviter),
                              'inviter_email': collaboration_invite.inviter.email,
                              'invitee_name': cls.address_user(collaboration_invite.invitee),
                              'document_title': collaboration_invite.document.title,
                              'follow_url': follow_url,
                              'sentence_text': sent_text})

    @classmethod
    def send_user_was_mentioned(cls, mention_author, mentioned_user,
                                sentence, sentence_index):
        """
        Notify a user that he/she was mentioned in a document
        :param mention_author: User, who created comment with mention
        :param mentioned_user: User, to whom mention email should be sent
        :param document: The document containing comment with mention
        :param sentence: Commented sentence
        :return: True if email was sent, False otherwise
        """
        from core.tools import login_resource_url

        document = sentence.doc
        subject = "%s mentioned you in %s" % (
            cls.address_user(mention_author),
            document.title
        )
        template = 'email/document_mention.html'
        html_template = 'email/html/document_mention.html'

        report_url = absolutify(
            login_resource_url(mentioned_user, sentence.get_report_url(sentence_index))
        )

        user_settings = UserSettings(mention_author)
        if user_settings.get_setting('include_clause_in_outcoming_mention_emails') and sentence:
            # Convert text with internal markers to some preformatted text
            sent_text = preformat_markers(sentence.text)
            # Add some large limit to avoid abuse
            sent_text = sent_text[:5000]
        else:
            sent_text = None

        return cls.send(to_email=mentioned_user.email,
                        from_email='Beagle.ai <noreply@beagle.ai>',
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'mention_author': cls.address_user(mention_author),
                              'mention_author_email': mention_author.email,
                              'mentioned_user': cls.address_user(mentioned_user),
                              'document_title': document.title,
                              'follow_url': report_url,
                              'sentence_text': sent_text})

    @classmethod
    def send_owner_changed(cls, old_owner, document):
        """
        Notify a user that him/she is the new owner of a document
        :param old_owner: The previous owner of the document
        :param document: The document with `document.owner` being the new owner
        :return: True if email was sent, False otherwise
        """

        subject = "%s assigned you owner of %s" % (
            cls.address_user(old_owner),
            document.title
        )

        template = 'email/owner_changed.html'
        html_template = 'email/html/owner_changed.html'

        return cls.send(to_email=document.owner.email,
                        from_email='Beagle.ai <noreply@beagle.ai>',
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'old_owner_name': cls.address_user(old_owner),
                              'new_owner_name': cls.address_user(document.owner),
                              'document_title': document.title,
                              'follow_url': absolutify(document.get_report_url())})

    @classmethod
    def send_password_request(cls, password_request, reset_url):
        logging.info('Sending email notification for password request: %s, reset_url=%s', password_request, reset_url)

        subject = "Reset password on Beagle.ai"
        template = 'email/request_password.html'
        html_template = 'email/html/request_password.html'

        return cls.send(to_email=password_request.user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={
                            'firstname': cls.address_user(password_request.user),
                            'follow_link': reset_url})

    @classmethod
    def document_complete_notification(cls, user, document, report_url):
        """
        Send a document analysis complete email notification
        :param user: the user model
        :param report_url: The URL the user should follow to see the completed report
        :return: True if email was sent, False otherwise
        """

        logging.info('Sending document complete notification for user=%s, report_url=%s', user, report_url)

        subject = "Beagle has processed your documents"
        template = 'email/document_processed.html'
        html_template = 'email/html/document_processed.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'follow_link': report_url,
                              'document_title': document.title,
                              'first_name': cls.address_user(user), })

    @classmethod
    def send_document_digest(cls, user, document, is_reanalysis=False):
        """
        Send a `document` analysis digest to the `user`
        :param user: A user Django model
        :param document: A core.models.Document model
        :param is_reanalysis: A flag indicating that the `document` was reanalyzed
        :return: True if email was sent, False otherwise
        """
        from core.tools import login_resource_url

        if not document.has_access(user):
            logging.warning("Trying to send an analysis digest via email "
                            "to a user that doesn't have access to the document, user=%s" % str(user))
            return

        digest = document.digest()

        if digest is None:
            return

        report_url = absolutify(login_resource_url(user, document.get_report_url()))

        logging.info('Sending document analysis digest to user=%s, report_url=%s', user, report_url)

        done_action = "reanalyzed" if is_reanalysis else "processed"

        subject = "Beagle has %s your document" % done_action

        if hasattr(settings, 'CLIENT_NAME') and getattr(settings, 'CLIENT_NAME') == 'WESTPAC':
            template = 'email/westpac/digest.html'
            html_template = 'email/westpac/html/digest.html'

            # Exclude empty grammar-based annotations
            digest['annotations'] = filter(lambda item: item['total'] > 0,
                                           digest['annotations'])

        else:
            template = 'email/digest.html'
            html_template = 'email/html/digest.html'

            # The original digest payload is too bulky, so trim it a bit

            digest['keywords'] = digest['keywords'][:settings.TOP_KEYWORD_COUNT_DIGEST]
            for kw_stats in digest['keywords']:
                kw_stats['clauses'] = kw_stats['clauses'][:settings.TOP_KEYWORD_CLAUSE_COUNT_DIGEST]
                kw_stats['xmore'] = kw_stats['total'] - len(kw_stats['clauses'])

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'follow_link': report_url,
                              'document_title': document.title,
                              'first_name': cls.address_user(user),
                              'is_owner': document.owner.pk == user.pk,
                              'done_action': done_action,
                              'digest': digest})

    @classmethod
    def send_batch_processed_notification(cls, user, batch):
        """
        Send a `batch` processed email notification to the `user`
        :param user: A user Django model
        :param batch: A core.models.Batch model
        :return: True if email was sent, False otherwise
        """
        from core.tools import login_resource_url

        if not batch.has_access(user):
            logging.warning("Trying to send a processed notification via email "
                            "to a user that doesn't have access to the batch, user=%s" % str(user))
            return

        report_url = absolutify(login_resource_url(user, batch.get_report_url()))

        logging.info('Sending batch processed notification to user=%s, report_url=%s', user, report_url)

        subject = "Beagle has processed your batch of documents"
        template = 'email/batch_processed.html'
        html_template = 'email/html/batch_processed.html'

        # Make sure that the set of the valid documents and
        # the set of the invalid documents don't intersect
        for invalid_document_id in batch.invalid_documents_ids:
            batch.remove_document(invalid_document_id)

        documents = [d.title for d in batch.get_documents()]
        invalid_documents = [i_d.title for i_d in batch.get_invalid_documents()]

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'follow_link': report_url,
                              'batch_name': batch.name,
                              'first_name': cls.address_user(user),
                              'documents': documents,
                              'invalid_documents': invalid_documents})

    @classmethod
    def document_uploaded_via_email_notification(cls, document):
        """
        Send a document analysis complete email notification
        :param document: the document the user uploaded via email
        :return: True if email was sent, False otherwise
        """
        user = document.owner

        logging.info('Sending document uploaded via email notification for user=%s', user)

        subject = "Beagle has received your document and will now process it."
        template = 'email/document_uploaded_via_email.html'
        html_template = 'email/html/document_uploaded_via_email.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'document_title': document.title,
                              'first_name': cls.address_user(user), })


    @classmethod
    def notification_reminders(cls, user, notifications):
        """
        :param user: The user to send the email to
        :param notifications: list of `Notification` objects
        :return: True if email was sent, False otherwise
        """
        from core.tools import notification_to_dict, notification_url
        from dogbone.tools import absolutify

        logging.info('Sending notifications reminders for user=%s', user)

        subject = "You have some notifications on Beagle that may need your attention"
        template = 'email/notification_reminders.html'
        html_template = 'email/html/notification_reminders.html'

        serialized = [(notification_to_dict(n), notification_url(n), n.timestamp) for n in notifications]

        notifications = [{'avatar_url': absolutify(notif['actor']['avatar']),
                          'notification_display': notif['suggested_display'],
                          'notification_url': absolutify(notif_url),
                          'notification_timestamp': notif_timestamp}
                         for notif, notif_url, notif_timestamp in serialized]

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user),
                              'account_url': absolutify(reverse('account')),
                              'notifications': notifications})

    @classmethod
    def auto_account_creation_notification(cls, onetime_login):
        """
        When an account was created automatically, send an one-time login URL to the user via email
        :param onetime_login: The OneTimeLoginHash generated for the user
        :return: True if email was sent, False otherwise
        """
        user = onetime_login.user
        logging.info('Sending auto account creation notification for user=%s, onetime_login=%s', user, onetime_login)

        subject = "Meet Rufus: Your Automatic Contract Guide"
        template = 'email/auto_account_created.html'
        html_template = 'email/html/auto_account_created.html'

        follow_url = "%s?next=%s&hash=%s" % (reverse('login'), reverse('account'), onetime_login.get_hash())
        follow_url = absolutify(follow_url)

        return cls.send(to_email=user.email,
                        from_email=cls.SUPPORT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user),
                              'follow_url': follow_url})

    @classmethod
    def document_processing_error_notification(cls, document):
        """
        When we're not able to process a document we send an email to the user
        :param document: the Document that we weren't able to process
        :return: True if email was sent, False otherwise
        """
        user = document.owner
        logging.info('Sending document_processing_error_notification to user=%s, document=%s', user, document)

        subject = "We're having trouble processing your contract"
        template = 'email/document_processing_error.html'
        html_template = 'email/html/document_processing_error.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user),
                              'document_title': document.title})

    @classmethod
    def unsupported_file_type_error_notification(cls, user, title):
        """
        We're unable to process a certain file upload because of the file format
        :param user: The user that will receive the notification
        :param title: the original title of the document file
        :return: True if email was sent, False otherwise
        """

        logging.info('Sending unsupported_file_type_error_notification to user=%s, title=%s', user, title)

        subject = "We don't support this file type"
        template = 'email/file_type_error.html'
        html_template = 'email/html/file_type_error.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user),
                              'title': title})

    @classmethod
    def help_notification(cls, user):
        """
        We're unable to process a certain file upload because of the file format
        :param user: The user that will receive the notification
        :param title: the original title of the document file
        :return: True if email was sent, False otherwise
        """

        logging.info('Sending help_notification to user=%s', user)

        subject = "Help with Rufus"
        template = 'email/help.html'
        html_template = 'email/html/help.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user)})

    @classmethod
    def attachments_not_found_notification(cls, user):
        logging.info('Sending attachments_not_found_notification to user=%s', user)

        subject = "We couldn't find your attachments"
        template = 'email/attachments_not_found.html'
        html_template = 'email/html/attachments_not_found.html'

        return cls.send(to_email=user.email,
                        from_email=cls.DEFAULT_FROM_EMAIL,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        args={'first_name': cls.address_user(user)})
