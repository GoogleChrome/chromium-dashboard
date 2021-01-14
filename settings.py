from __future__ import division
from __future__ import print_function

import logging
import os

from google.appengine.api import app_identity


#Hack to get custom tags working django 1.3 + python27.
INSTALLED_APPS = (
  #'nothing',
  'customtags',
)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

TEMPLATES = [
  {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(ROOT_DIR, 'templates')],
    'APP_DIRS': True,
  },
]

# By default, send all email to an archive for debugging.
# For the live cr-status server, this setting is None.
SEND_ALL_EMAIL_TO = 'cr-status-staging-emails+%(user)s+%(domain)s@google.com'

BOUNCE_ESCALATION_ADDR = 'cr-status-bounces@google.com'

################################################################################

PROD = False
DEBUG = True
SEND_EMAIL = False  # Just log email
DEV_MODE = os.environ['SERVER_SOFTWARE'].startswith('Development')
UNIT_TEST_MODE = os.environ['SERVER_SOFTWARE'].startswith('test')


APP_ID = app_identity.get_application_id()
SITE_URL = 'http://%s.appspot.com/' % APP_ID
CLOUD_TASKS_REGION = 'us-central1'

if APP_ID == 'testbed-test':
  APP_TITLE = 'Local testing'
  SITE_URL = 'http://127.0.0.1:8888/'
elif DEV_MODE:
  PROD = False
  APP_TITLE = 'Chrome Status Dev'
  SITE_URL = 'http://127.0.0.1:8888/'
elif APP_ID == 'cr-status':
  PROD = True
  DEBUG = False
  APP_TITLE = 'Chrome Platform Status'
  SEND_EMAIL = True
  SEND_ALL_EMAIL_TO = None  # Deliver it to the intended users
  SITE_URL = 'http://chromestatus.com/'
elif APP_ID == 'cr-status-staging':
  SEND_EMAIL = True
  APP_TITLE = 'Chrome Platform Status Staging'
else:
  logging.error('Unexpected app ID %r, please configure settings.py.', APP_ID)

SECRET_KEY = os.environ['DJANGO_SECRET']

APP_VERSION = os.environ['CURRENT_VERSION_ID'].split('.')[0]

RSS_FEED_LIMIT = 15

VULCANIZE = True #PROD

DEFAULT_CACHE_TIME = 60 # seconds

USE_I18N = False

TEMPLATE_DEBUG = DEBUG
if DEBUG:
  TEMPLATE_CACHE_TIME = 0
else:
  TEMPLATE_CACHE_TIME = 600 # seconds

SEND_PUSH_NOTIFICATIONS = PROD # Flag to turn off sending push notifications for all users.

FIREBASE_SERVER_KEY = os.environ.get('FIREBASE_SERVER_KEY')
