import json
import urllib
import logging
import requests
import syslog

# Project
from server.models import Detail

logger = logging.getLogger(__name__)


#######################################################################################################################
#
# Internal API Wrapper
#
#######################################################################################################################


class InternalAPI:
    """
    Wrapper class over the internal Beagle API
    Note: the requests have to be made from the internal network and the machine hosting Django has to have the
    IP of the source machine (the one using this class) in the INTERNAL_IPS list
    """

    ENVS = {
        'DEV': {
            'DOMAIN': 'dev.beagle.ai',
            'PROTOCOL': 'https',
        },
        'STAGING': {
            'DOMAIN': 'staging.beagle.ai',
            'PROTOCOL': 'https',
        },
        'BETA': {
            'DOMAIN': 'beta.beagle.ai',
            'PROTOCOL': 'https',
        },
        'LOCAL': {
            'DOMAIN': 'localhost:8000',
            'PROTOCOL': 'http',
        }
    }

    def __init__(self, email_domain):
        if not Detail.objects.filter(email_domain=email_domain).exists():
            from exceptions import WrongEnvironmentException
            raise WrongEnvironmentException("The domain for that email has not been configured on the server")

        detail = Detail.objects.filter(email_domain=email_domain).first()
        self.protocol = detail.endpoint_protocol
        self.domain = detail.endpoint_domain

    @property
    def API_ENDPOINT_USER(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user/%s'

    @property
    def API_ENDPOINT_USER_CREATE(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user?send_auto_create=true'

    @property
    def API_ENDPOINT_DOCUMENT_UPLOAD(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/document/upload?from=%s&send_upload_via_email=true'

    @property
    def API_ENDPOINT_SUBSCRIPTION_CREATE(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user/%s/subscription/%s'

    @property
    def API_SEND_UNSUPPORTED_FILE_TYPE_NOTIFICATION(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user/%s/notify/unsupported_file_type'

    @property
    def API_SEND_HELP_NOTIFICATION(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user/%s/notify/help'

    @property
    def API_SEND_ATTACHMENTS_NOT_FOUND_NOTIFICATION(self):
        return self.protocol + '://' + self.domain + '/api/v1/_internal/user/%s/notify/attachments_not_found'

    def ping_server(self, user_email):
        url = self.protocol + '://' + self.domain + '/api/v1/document/ping/'
        response = requests.post(url, data={'email': user_email})

        if response.status_code == 200:
            logger.info(response.content)
            return

        from exceptions import StrangeBehaviourException
        raise StrangeBehaviourException("Undocumented response status code on %s" % url)

    def get_user(self, user_addr):
        """
        GET the user details through the internal Beagle API
        """
        url = self.API_ENDPOINT_USER % urllib.quote(user_addr)
        response = requests.get(url)
        if response.status_code == 404:
            logger.warning("User with email=%s not found" % user_addr)
            return None

        if response.status_code == 200:
            return json.loads(response.content)

        from exceptions import StrangeBehaviourException
        raise StrangeBehaviourException("Undocumented response status code on %s" % url)

    def create_user(self, user_addr):
        """
        Create a user via the internal Beagle API.
        The password will be automatically assigned
        """
        logger.info("Attempting to create an new user with email=%s" % user_addr)
        url = self.API_ENDPOINT_USER_CREATE

        response = requests.post(url, data=json.dumps({'email': user_addr}),
                                 headers={'Content-type': 'application/json'})

        if response.status_code != 200:
            logger.error("The create user API endpoint call failed with: status=%s, payload=%s" %
                         (response.status_code, str(response.content)))
            return None

        try:
            user = json.loads(response.content)
            if isinstance(user, list):
                user = user[0]

            return user
        except ValueError:
            logger.error("Could not decode json from content=%s" % response.content)
            return None

    def upload_document(self, user_addr, files_dict):
        """
        Upload documents via the internal Beagle API.
        The format for `files_dict` is {'file_name.txt': <InMemoryFile>}
        """
        url = self.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote(user_addr)

        logger.info("Uploading document to URL=%s" % url)
        syslog.syslog("%s" % files_dict)
        response = requests.post(url, files=files_dict, )

        logger.info("Upload STATUS_CODE=%s URL=%s" % (response.status_code, url))
        logger.info("RESPONSE=%s" % str(response.content))

        return json.loads(response.content)

    def upload_url(self, user_addr, url):
        """
        Upload documents via the internal Beagle API.
        :param user_addr: The user's email address
        :param title: The title of the uploaded document
        :param url: The url of the uploaded document
        :return: API result dict
        """

        api_url = self.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote(user_addr)

        logger.info("Uploading document via url for user=%s" % user_addr)
        response = requests.post(api_url,
                                 data=json.dumps({'url': url}),
                                 headers={'Content-type': 'application/json'})
        logger.info("Upload status_code=%s api_url=%s" % (response.status_code, api_url))

        return json.loads(response.content)

    def upload_text(self, user_addr, title, text):
        """
        Upload documents via the internal Beagle API.
        :param user_addr: The user's email address
        :param title: The title of the uploaded document
        :param text: The content of the document
        :return: API result dict
        """

        api_url = self.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote(user_addr)

        logger.info("Uploading document via content for user=%s" % user_addr)
        response = requests.post(api_url,
                                 data=json.dumps({'title': title, 'text': text}),
                                 headers={'Content-type': 'application/json'})
        logger.info("Upload status_code=%s api_url=%s" % (response.status_code, api_url))

        return json.loads(response.content)

    def create_subscription(self, user_addr):
        url = self.API_ENDPOINT_SUBSCRIPTION_CREATE % (urllib.quote(user_addr), urllib.quote('ALL_ACCESS_TRIAL'))
        response = requests.post(url)
        if response.status_code == 200:
            try:
                return json.loads(response.content)
            except ValueError:
                logger.error("Could not load subscription from json=%s" % response.content)
                return None

        logger.error("Error on subscription creation endpoint status_code=%s, payload=%s" % (response.status_code, response.content))
        return None

    def send_unsupported_file_type_notification(self, user_addr, document_title):
        url = self.API_SEND_UNSUPPORTED_FILE_TYPE_NOTIFICATION % urllib.quote(user_addr)
        response = requests.post(url, data=json.dumps({'title': document_title}),
                                 headers={'Content-type': 'application/json'})

        if response.status_code != 200:
            logger.error('Could not send the unsupported file type notification to user=%s for file=%s' % (user_addr, document_title))

    def send_help_notification(self, user_addr):
        url = self.API_SEND_HELP_NOTIFICATION % urllib.quote(user_addr)
        response = requests.post(url, headers={'Content-type': 'application/json'})

        if response.status_code != 200:
            logger.error('Could not send help notification to user=%s' % user_addr)

    def send_attachments_not_found(self, user_addr):
        url = self.API_SEND_ATTACHMENTS_NOT_FOUND_NOTIFICATION % urllib.quote(user_addr)
        response = requests.post(url, headers={'Content-type': 'application/json'})

        if response.status_code != 200:
            logger.error('Could not send attachments not found notification to user=%s' % user_addr)
