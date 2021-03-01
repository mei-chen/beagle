import re
import os
import quopri
import logging
import StringIO
from bs4 import BeautifulSoup
from settings import DOCUMENT_INDEX, DOCUMENT_REPOSITORY_PATH, ACCEPTED_EXTENSIONS

logger = logging.getLogger('RufusLogger')

#######################################################################################################################
#
# Utils & Tools
#
#######################################################################################################################


def extract_addr(text):
    """
    Extract the email address from a text
    :param text: the string
    :return: email
    """

    match = re.search(r'[\w\.\-_\+]+@[\w\.\-_]+', text)
    if match:
        return match.group(0)
    return None


# def extract_body(msg):
#     body = ""
#
#     if msg.is_multipart():
#         for part in msg.walk():
#             ctype = part.get_content_type()
#             cdispo = str(part.get('Content-Disposition'))
#
#             # skip any text/plain (txt) attachments
#             if ctype == 'text/plain' and 'attachment' not in cdispo:
#                 body = part.get_payload(decode=True)  # decode
#                 break
#     # not multipart - i.e. plain text, no attachments, keeping fingers crossed
#     else:
#         body = msg.get_payload(decode=True)
#
#     return body


def get_body(msg):
    """
    Extract the main content from an email message
    :param msg: The email payload
    :return: the email body
    """

    body = ""

    def clean_part(part):
        part = quopri.decodestring(part)
        part = part.replace('<br>', os.linesep)
        part = part.replace('<br/>', os.linesep)
        part = part.replace('<br />', os.linesep)

        soup = BeautifulSoup(part, 'lxml')
        part = soup.get_text()
        return part

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    part_body = part.get_payload(decode=True) + os.linesep  # decode
                    body += clean_part(part_body) + os.linesep
                except Exception as e:
                    logger.exception(str(e))

    else:
        body = clean_part(msg.get_payload(decode=True))
    return body


def get_attachments(msg):
    """
    Get a dictionary of attachments from an email message
    :param msg: The email payload
    :return: {'filename.docx': <InMemoryFile>}
    """
    attachments = {}
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        if filename is not None:
            logger.info("Found attachment=%s" % filename)
            extension = filename.split('.')[-1]
            if extension.lower() not in ACCEPTED_EXTENSIONS:
                continue

            attachments[filename] = part.get_payload(decode=True)

    # Make attachments in memory files
    file_attachments = {}
    for fname, c_attachment in attachments.iteritems():
        str_file = StringIO.StringIO()
        str_file.write(c_attachment)
        str_file.seek(0)
        file_attachments[fname] = str_file

    return file_attachments


def get_default_document(phrase):
    """
    Retrieve a default document from the repository given a phrase
    :param phrase: Example: `Twitter TOS`
    :return: (None, None) or (opened File, file name)
    """

    canonical_phrase = re.sub(' +', ' ', phrase.lower())
    logger.info("Searching for canonical phrase = '%s'" % canonical_phrase)
    for file_name, file_details in DOCUMENT_INDEX.iteritems():
        if canonical_phrase in file_details['key_phrases']:
            try:
                file_path = os.path.join(DOCUMENT_REPOSITORY_PATH, file_name)
                document = open(file_path, 'rb')
                return document, file_details['title']
            except IOError as ioe:
                logger.error('Could not open default document: "%s"', str(ioe))
                return None, None

    return None, None

