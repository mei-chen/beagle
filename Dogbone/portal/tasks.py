import PyPDF2
import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User

from integrations.hubspot import HubspotAPI
from integrations.intercom_api import IntercomAPI
from keywords.models import SearchKeyword


@shared_task
def hubspot_submit_form(form_id, url, ip, hutk, page_name, data):
    from django.conf import settings
    if settings.DEBUG is False:

        hubspot = HubspotAPI(portal_id=settings.HUBSPOT_PORTAL_ID)
        return hubspot.submit_form(form_id, url, ip, hutk, page_name, data)

@shared_task
def hubspot_get_vid(email):
    """
    Hit the hubspot API to update a contact given their vid
    :param email: The user to be updated's email
    :return: User's hubspot vid #
    """
    from django.conf import settings
    if settings.DEBUG is False:
        hubspot = HubspotAPI(api_key=settings.HUBSPOT_API_KEY)
        return hubspot.get_contact_vid(email)

@shared_task
def hubspot_update_contact_properties(email, data):
    """
    Hit the hubspot API to update a contact given their vid
    :param vid: The user to be updated hubspot vid #
    :data: an array of dictionaries containing property, value pairs to update e.g.
    [
        {
            "property": "email",
            "value": "new-email@hubspot.com"
        },
        {
            "property": "firstname",
            "value": "Updated",
            "timestamp": 1419284759000
        }
    ]
    :return: True/False
    """
    from django.conf import settings
    if settings.DEBUG is False:
        vid = hubspot_get_vid(email)
        hubspot = HubspotAPI(api_key=settings.HUBSPOT_API_KEY)
        return hubspot.update_contact_properties(vid, data)


@shared_task
def update_PDFUploadMonitor(fpath, need_ocr):
    from portal.models import PDFUploadMonitor

    # Keep the record
    if len(PDFUploadMonitor.objects.all()) == 0:
        stat = PDFUploadMonitor()
        stat.save()
    else:
        stat = PDFUploadMonitor.objects.latest()

    # Add page count
    with open(fpath, "rb") as pdfin:
        reader = PyPDF2.PdfFileReader(pdfin)
        stat.add_doc(pages=reader.getNumPages(), ocr=need_ocr)


@shared_task
def send_intercom_inapp_message(from_id, to_email, message):
    """
    Send an intercom inapp message
    :param from_id: The user sending the message
    :param to_email: The application user receiving the message
    :param message: The actual message
    :return: True/False
    """
    api = IntercomAPI(settings.INTERCOM_APP_ID, settings.INTERCOM_API_KEY)
    try:
        api.send_message(from_id, to_email, message)
        return True
    except:
        return False


@shared_task
def add_keyword_to_cache(keyword_id):
    """
    Adds the `SearchKeyword.keyword` to the `UserDetails.keywords_cache`
    :param keyword_id: the PK of the `SearchKeyword`
    :return:
    """

    try:
        kw = SearchKeyword.objects.get(pk=keyword_id)
        kw.owner.details.add_keyword(kw.keyword)
    except SearchKeyword.DoesNotExist:
        logging.error("'add_keyword_to_cache' called with an invalid keyword_id=%s" % keyword_id)

@shared_task
def remove_keyword_from_cache(user_id, keyword):
    """
    Removes a keyword from the `UserProfile.keyword_cache`
    :param user_id: The id of the owning user of the `SearchKeyword`
    :param keyword: The keyword string
    :return:
    """
    try:
        user = User.objects.get(pk=user_id)
        user.details.remove_keyword(keyword)
    except User.DoesNotExist:
        pass
