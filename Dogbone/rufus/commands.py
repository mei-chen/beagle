import logging
import validators
from email.utils import parseaddr
from tools import get_attachments, get_default_document, get_body
from settings import MINIMUM_BODY_LENGTH_FOR_ANALYSIS


logger = logging.getLogger('RufusLogger')


class RufusCommand:
    def __init__(self, message, environment='LOCAL', **kwargs):
        self.message = message
        self.environment = environment

    def user_email(self):
        fullname, from_address = parseaddr(self.message.get('From'))

        return from_address

    def execute(self):
        pass


class CommandMissingException(Exception):
    pass


class AbstractRufusCommandDispatcher:
    """
    Select the appropriate command for a given email message and dispatch
    """

    def __init__(self, message, environment='LOCAL', **kwargs):
        self.message = message
        self.kwargs = kwargs
        self.environment = environment
        self.command = None

        self.command = self.select()

    def select(self):
        pass

    def dispatch(self):
        if self.command is None:
            raise CommandMissingException("A command could not be selected")

        assert callable(self.command)

        return self.command(self.message, self.environment, **self.kwargs).execute()


class AttachmentProcessCommand(RufusCommand):
    """
    Extract Attachments and process them
    """
    def execute(self):
        attachments = get_attachments(self.message)
        from api import InternalAPI
        api = InternalAPI(env=self.environment)
        result = api.upload_document(self.user_email(), attachments)
        return result


class SubjectURLProcessCommand(RufusCommand):
    """
    If the subject is an URL, forward the URL to Beagle to extract the content and process it
    """
    def execute(self):
        url = self.message.get('Subject')
        from api import InternalAPI
        api = InternalAPI(env=self.environment)
        result = api.upload_url(self.user_email(), url)
        return result


class BodyProcessCommand(RufusCommand):
    """
    The document is included in the email's body
    """
    def execute(self):
        title = self.message.get('Subject')
        body = get_body(self.message)
        from api import InternalAPI
        api = InternalAPI(env=self.environment)
        result = api.upload_text(self.user_email(), title, body)
        return result


class HelpCommand(RufusCommand):
    """
    Provide a quick tutorial of Rufus
    """
    def execute(self):
        from api import InternalAPI
        api = InternalAPI(env=self.environment)
        return api.send_help_notification(self.user_email())


class DefaultDocumentProcessCommand(RufusCommand):
    """
    Pick a default document from the library and process it
    """
    def execute(self):
        from api import InternalAPI
        subject = self.message.get('Subject').strip()
        default_document, default_file_name = get_default_document(subject)
        api = InternalAPI(env=self.environment)
        result = api.upload_document(self.user_email(), {default_file_name: default_document})
        return result


class DocumentNotFoundAlertCommand(RufusCommand):
    """
    Alert the user that we couldn't find an attachment that can be processed
    """
    def execute(self):
        from api import InternalAPI
        api = InternalAPI(env=self.environment)
        return api.send_attachments_not_found(self.user_email())


class RufusCommandDispatcher(AbstractRufusCommandDispatcher):
    def select(self):
        subject = self.message.get('Subject').strip()

        if subject.lower() in ['help', 'help!', 'help me']:
            logger.info('Issuing HelpCommand')
            return HelpCommand

        if validators.url(subject.lower()):
            logger.info('Issuing SubjectURLProcessCommand')
            return SubjectURLProcessCommand

        default_document, default_title = get_default_document(subject)
        if default_document is not None:
            logger.info('Issuing DefaultDocumentProcessCommand')
            return DefaultDocumentProcessCommand

        attachments = get_attachments(self.message)

        if attachments:
            logger.info('Issuing AttachmentProcessCommand')
            return AttachmentProcessCommand

        body = get_body(self.message)
        if len(body) >= MINIMUM_BODY_LENGTH_FOR_ANALYSIS:
            logger.info('Issuing BodyProcessCommand')
            return BodyProcessCommand

        logger.info('Issuing DocumentNotFoundAlertCommand')
        return DocumentNotFoundAlertCommand








