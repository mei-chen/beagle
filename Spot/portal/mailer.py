from django.conf import settings
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import get_template
from django.urls import reverse
from six.moves.urllib.parse import urlencode, urljoin


class Mailer(object):

    @classmethod
    def send(cls, from_email, to_email, subject,
             template, html_template, **kwargs):

        recipient_list = [to_email]

        context = Context(kwargs)
        message = get_template(template).render(context)
        html_message = get_template(html_template).render(context)

        fail_silently = not settings.DEBUG

        status = send_mail(subject=subject,
                           message=message,
                           from_email=from_email,
                           recipient_list=recipient_list,
                           fail_silently=fail_silently,
                           html_message=html_message)

        return bool(status)


class SpotMailer(Mailer):
    NOREPLY_FROM_EMAIL = 'noreply@beagle.ai'

    @staticmethod
    def address_receiver(user):
        return user.first_name or user.username

    @staticmethod
    def address_sender(user):
        user_full_name = user.get_full_name() or user.username
        if user.email and user_full_name != user.email:
            user_full_name += ' (%s)' % user.email
        return user_full_name

    @classmethod
    def send_dataset_collaboration_invite(cls, invite, domain):
        from_email = 'Spot Collaboration Invitation <%s>' % \
                     cls.NOREPLY_FROM_EMAIL
        to_email = invite.invitee.email
        subject = '%s invited you to collaborate on Spot' % \
                  cls.address_sender(invite.inviter)
        template = 'email/dataset_collaboration_invite.html'
        html_template = 'email/html/dataset_collaboration_invite.html'

        kwargs = {
            'invitee': cls.address_receiver(invite.invitee),
            'inviter': cls.address_sender(invite.inviter),
            'dataset': invite.dataset.name,
            'collaboration_url': urljoin(domain, '/datasets/%d/page/1' %
                                         invite.dataset.pk),
        }

        return cls.send(to_email=to_email,
                        from_email=from_email,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        **kwargs)

    @classmethod
    def send_dataset_external_invite(cls, invite, domain):
        from_email = 'Spot Collaboration Invitation <%s>' % \
                     cls.NOREPLY_FROM_EMAIL
        to_email = invite.email
        subject = '%s invited you to collaborate on Spot' % \
                  cls.address_sender(invite.inviter)
        template = 'email/dataset_external_invite.html'
        html_template = 'email/html/dataset_external_invite.html'

        kwargs = {
            'inviter': cls.address_sender(invite.inviter),
            'dataset': invite.dataset.name,
            'registration_url': urljoin(domain, reverse('account_signup')) +
                                '?' + urlencode({'email': invite.email}),
            'collaboration_url': urljoin(domain, '/datasets/%d/page/1' %
                                         invite.dataset.pk),
        }

        return cls.send(to_email=to_email,
                        from_email=from_email,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        **kwargs)

    @classmethod
    def send_experiment_collaboration_invite(cls, invite, domain):
        from_email = 'Spot Collaboration Invitation <%s>' % \
                     cls.NOREPLY_FROM_EMAIL
        to_email = invite.invitee.email
        subject = '%s invited you to collaborate on Spot' % \
                  cls.address_sender(invite.inviter)
        template = 'email/experiment_collaboration_invite.html'
        html_template = 'email/html/experiment_collaboration_invite.html'

        kwargs = {
            'invitee': cls.address_receiver(invite.invitee),
            'inviter': cls.address_sender(invite.inviter),
            'experiment': invite.experiment.name,
            'collaboration_url': urljoin(domain, '/experiments/%d/edit' %
                                         invite.experiment.pk),
        }

        return cls.send(to_email=to_email,
                        from_email=from_email,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        **kwargs)

    @classmethod
    def send_experiment_external_invite(cls, invite, domain):
        from_email = 'Spot Collaboration Invitation <%s>' % \
                     cls.NOREPLY_FROM_EMAIL
        to_email = invite.email
        subject = '%s invited you to collaborate on Spot' % \
                  cls.address_sender(invite.inviter)
        template = 'email/experiment_external_invite.html'
        html_template = 'email/html/experiment_external_invite.html'

        kwargs = {
            'inviter': cls.address_sender(invite.inviter),
            'experiment': invite.experiment.name,
            'registration_url': urljoin(domain, reverse('account_signup')) +
                                '?' + urlencode({'email': invite.email}),
            'collaboration_url': urljoin(domain, '/experiments/%d/edit' %
                                         invite.experiment.pk),
        }

        return cls.send(to_email=to_email,
                        from_email=from_email,
                        subject=subject,
                        template=template,
                        html_template=html_template,
                        **kwargs)
