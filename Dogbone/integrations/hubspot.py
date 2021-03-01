import json
import logging
from requests import Request, Session


class HubspotAPIError(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)


class HubspotAPI:
    """
    Convenient class for performing certain interactions with HubSpot CRM
    """
    def __init__(self, portal_id=None, api_key=None):
        self.PORTAL_ID = portal_id
        self.API_KEY = api_key

    @classmethod
    def post_form(cls, hs_url, data):
        """
        :param hs_url: The HubSpot url where to post the data
        :param data: the data we post to the form
        :return: True/False
        """

        s = Session()

        req = Request('POST', hs_url, data=data)
        prepped = req.prepare()
        response = s.send(prepped)

        if response.status_code != 204:
            logging.error('Error encountered while posting data: %s to HubSpot: %s' % (data, response.content))
            return False

        logging.info('Successfully posted data: %s to HubSpot hs_url=%s' % (str(data), hs_url))
        return True

    def build_form_url(self, form_id):
        """
        Build the form url, given the id of the form
        :param form_id: the UUID of the form
        :return: the url
        """
        return 'https://forms.hubspot.com/uploads/form/v2/%s/%s' % (self.PORTAL_ID, form_id)

    def build_context(self, url=None, ip=None, hutk=None, page_name=None):
        """
        Build the HubSpot context
        :return: context dict
        """
        hs_context = {}
        if hutk:
            hs_context['hutk'] = hutk

        if ip:
            hs_context['ipAddress'] = ip

        if url:
            hs_context['pageUrl'] = url

        if page_name:
            hs_context['pageName'] = page_name

        return hs_context

    def submit_form(self, form_id, url=None, ip=None, hutk=None, page_name=None, data=None):
        """
        Submit a HubSpot form
        :param form_id: the UUID of the form
        :param url: the url from where the form was submitted
        :param ip: the IP that made the request
        :param hutk: HubSpot Token
        :param page_name: the name of the page
        :param data: dict with extra data we want sent (form field values)
        :return: True/False
        """

        if self.PORTAL_ID is None:
            raise HubspotAPIError('Please provide the hubspot PORTAL_ID')

        hs_url = self.build_form_url(form_id)
        hs_context = self.build_context(url, ip, hutk, page_name)
        hs_context_json = json.dumps(hs_context)

        hs_data = {'hs_context': hs_context_json}

        if data:
            hs_data.update(data)

        return self.post_form(hs_url, hs_data)

    @classmethod
    def post_hubspot_api(cls, hs_url, hs_data):
        """
        :param hs_url: The HubSpot url where to post the data
        :param data: the data we post to the endpoint
        :return: True/False
        """
        s = Session()

        req = Request('POST', hs_url, data=hs_data)
        prepped = req.prepare()
        response = s.send(prepped)

        if response.status_code != 204:
            logging.error('Error encountered while posting data: %s to HubSpot: %s' % (hs_data, response.content))
            return False

        logging.info('Successfully posted data: %s to HubSpot hs_url=%s' % (str(hs_data), hs_url))
        return True

    def build_update_contact_properties_url(self, vid):
        """
        Build the form url, given the id of the form
        :param form_id: the UUID of the form
        :return: the url
        """
        return 'https://api.hubapi.com/contacts/v1/contact/vid/%s/profile?hapikey=%s' % (vid, self.API_KEY)

    def build_get_contact_vid_url(self, email):
        """
        Build the url to request a hubspot user based on email. We need to retrieve the vid so we can update the user within hubspot.
        :param email: user's email to be queried in HubSpot
        :return: the request url
        """
        return 'https://api.hubapi.com/contacts/v1/contact/email/%s/profile?hapikey=%s&property=vid&formSubmissionMode=none&showListMemberships=false' % (email, self.API_KEY)

    def get_contact_vid(self, email):
        """
        Returns a contact's hubspot vID given an email
        :param email: user's email whose vID is required
        :return: the user's vID
        """
        # catch no API_KEY set
        if self.API_KEY is None:
            raise HubspotAPIError('Please provide the hubspot API_KEY')

        s = Session()
        hs_url = self.build_get_contact_vid_url(email)

        req = Request('GET', hs_url)
        prepped = req.prepare()
        response = s.send(prepped)

        if response.status_code == 404:
            logging.error('User email=%s not found in HubSpot: %s' % (email, response.content))
            return False

        if response.status_code != 200:
            logging.error('Error encountered while fetching data: email=%s to HubSpot: %s' % (email, response.content))
            return False

        vid = json.loads(response.content)['vid']

        return vid

    def update_contact_properties(self, vid, data=None):
        """
        Submit a HubSpot form
        :param vid: the hubspot contact's vid #
        :param data: array of dictionaries with property, data pairs
        :return: True/False
        """

        # Catch no API_KEY set
        if self.API_KEY is None:
            raise HubspotAPIError('Please provide the hubspot API_KEY')

        logging.info('Posting profile update to hubspot vid=%s' % (vid))

        hs_url = self.build_update_contact_properties_url(vid)

        properties_data = {}
        properties_data['properties'] = data
        hs_data = json.dumps(properties_data)

        return self.post_hubspot_api(hs_url, hs_data)
