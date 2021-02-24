import os
import logging
import logging.handlers

#######################################################################################################################
#
# Settings
#
#######################################################################################################################

ACCEPTED_EXTENSIONS = ('txt', 'pdf', 'docx', 'doc')

# file paths
file_path = os.path.dirname(os.path.realpath(__file__))
log_path = os.path.join(file_path, 'rufus.log')

# logger settings
logger = logging.getLogger('RufusLogger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# logger file handler
fh = logging.handlers.RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

DOCUMENT_REPOSITORY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'documents')

DOCUMENT_INDEX = {
    'Google_Construction_Agreement.txt': {
        'title': 'Google Construction Agreement.txt',
        'key_phrases': ['google construction agreement'],   # key phrases should only be lowercase and single spaced
    },
    'Twitter_TOS.txt': {
        'title': 'Twitter Terms of Service.txt',
        'key_phrases': ['twitter tos', 'twitter terms', 'twitter terms of service', 'twitter service terms']
    },
    'ACME master construction agreement.docx': {
        'title': 'Acme Master Construction Services Agreement.docx',
        'key_phrases': ['construction', 'acme', 'ace', 'construction agreement'],
    },
    'BoAVISAMC.docx': {
        'title': 'Bank of America Standard VISA and Mastercard Agreement.docx',
        'key_phrases': ['visa', 'mastercard', 'mc'],
    },
    'paypal.docx': {
        'title': 'PayPal Terms and Conditions.docx',
        'key_phrases': ['paypal', 'paypal terms', 'paypal terms and conditions'],
    },
    'itunes_uk.docx': {
        'title': 'iTunes UK Terms and Conditions.docx',
        'key_phrases': ['itunes uk', 'itunes england', 'uk itunes'],
    },
    'itunes_ca.docx': {
        'title': 'iTunes Canada Terms and Conditions.docx',
        'key_phrases': ['itunes ca', 'itunes canada', 'canada itunes'],
    },
    'itunes_usa.docx': {
        'title': 'iTunes USA Terms and Conditions.docx',
        'key_phrases': ['itunes usa', 'itunes u.s.a.', 'itunes', 'usa itunes'],
    }

}

MINIMUM_BODY_LENGTH_FOR_ANALYSIS = 200