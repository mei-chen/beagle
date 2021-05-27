import os
import socket
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

# This file describes all the custom settings
PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))

SAMPLE_DOCS_DIR = os.path.join(PROJECT_ROOT, 'resources', 'init_samples')

######################################################################################
#
#  UI SETTINGS
#
######################################################################################

# How many new comments to load when pushing `more` on comments widget
COMMENTS_PER_PAGE = 5

# How many most frequent keywords to show in document digest
TOP_KEYWORD_COUNT_DIGEST = 5

# How many clauses to preview for each top keyword in document digest
TOP_KEYWORD_CLAUSE_COUNT_DIGEST = 3

HOT_LOAD = os.environ.get("HOT_LOAD", 'True') == 'True'

######################################################################################
#
#  SOCKET
#
######################################################################################

NODEJS_SERVER = os.environ.get("SOCKET_DOMAIN", "localhost:4003")

