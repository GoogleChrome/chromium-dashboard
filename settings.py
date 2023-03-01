import logging
import os
from typing import Any, Optional


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_flask_template_path() -> str:
  """Returns a path to the templates.
  """
  return os.path.join(ROOT_DIR, 'templates')

# By default, send all email to an archive for debugging.
# For the live cr-status server, this setting is None.
SEND_ALL_EMAIL_TO: Optional[str] = (
    'cr-status-staging-emails+%(user)s+%(domain)s@google.com')

BOUNCE_ESCALATION_ADDR = 'cr-status-bounces@google.com'


# Display a site maintenance banner on every page.  Or, an empty string.
BANNER_MESSAGE = ''

# Timestamp used to notify users when the read only mode or other status
# described in the banner message takes effect.  Or, None.  It is
# expressed as a tuple of ints: (year, month, day[, hour[, minute[, second]]])
# e.g. (2009, 3, 20, 21, 45) represents March 20 2009 9:45PM UTC.
BANNER_TIME = None

# If a feature entry does not specify a component, use this one.
DEFAULT_COMPONENT = 'Blink'

# The default component for enterprise features.
DEFAULT_ENTERPRISE_COMPONENT = 'Enterprise'


################################################################################

PROD = False
STAGING = False
DEBUG = True
SEND_EMAIL = False  # Just log email
DEV_MODE = (os.environ['SERVER_SOFTWARE'].startswith('Development') or
            os.environ.get('GAE_ENV', '').startswith('localdev'))
UNIT_TEST_MODE = os.environ['SERVER_SOFTWARE'].startswith('test')

if not UNIT_TEST_MODE:
  # Py3 defaults to level WARN.
  logging.basicConfig(level=logging.INFO)


#setting GOOGLE_CLOUD_PROJECT manually in dev mode
if DEV_MODE or UNIT_TEST_MODE:
  APP_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'dev')
else:
  APP_ID = os.environ['GOOGLE_CLOUD_PROJECT']

SITE_URL = 'https://%s.appspot.com/' % APP_ID
CLOUD_TASKS_REGION = 'us-central1'

GOOGLE_SIGN_IN_CLIENT_ID = (
    '914217904764-enfcea61q4hqe7ak8kkuteglrbhk8el1.'
    'apps.googleusercontent.com')

# This is where the an anon user is redirected if they try to access a
# page that requires being signed in.
LOGIN_PAGE_URL = '/features?loginStatus=False'

INBOUND_EMAIL_ADDR = 'chromestatus@cr-status-staging.appspotmail.com'

# This is where review comment emails are sent:
REVIEW_COMMENT_MAILING_LIST = 'jrobbins-test@googlegroups.com'

# Truncate some log lines to stay under limits of Google Cloud Logging.
MAX_LOG_LINE = 200 * 1000


if UNIT_TEST_MODE:
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
  SITE_URL = 'https://chromestatus.com/'
  GOOGLE_SIGN_IN_CLIENT_ID = (
      '999517574127-7ueh2a17bv1ave9thlgtap19pt5qjp4g.'
      'apps.googleusercontent.com')
  INBOUND_EMAIL_ADDR = 'chromestatus@cr-status.appspotmail.com'
  REVIEW_COMMENT_MAILING_LIST = 'blink-dev@chromium.org'
  BACKUP_BUCKET = 'cr-status-backups'
elif APP_ID == 'cr-status-staging':
  STAGING = True
  SEND_EMAIL = True
  APP_TITLE = 'Chrome Platform Status Staging'
  BACKUP_BUCKET = 'cr-staging-backups'
else:
  logging.error('Unexpected app ID %r, please configure settings.py.', APP_ID)

RSS_FEED_LIMIT = 15

DEFAULT_CACHE_TIME = 3600 # seconds

USE_I18N = False

TEMPLATE_DEBUG = DEBUG
if DEBUG:
  TEMPLATE_CACHE_TIME = 0
else:
  TEMPLATE_CACHE_TIME = 600 # seconds
