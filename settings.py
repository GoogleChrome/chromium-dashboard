import os

#Hack to get custom tags working django 1.3 + python27.
INSTALLED_APPS = (
  #'nothing',
  'customtags',
)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

TEMPLATE_DIRS = (
  os.path.join(ROOT_DIR, 'templates')
)
################################################################################

if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
    os.getenv('SETTINGS_MODE') == 'prod'):
  PROD = True
else:
  PROD = False

DEBUG = not PROD
TEMPLATE_DEBUG = DEBUG

APP_TITLE = 'Chrome Platform Status'

APP_VERSION = os.environ['CURRENT_VERSION_ID'].split('.')[0]
MEMCACHE_KEY_PREFIX = APP_VERSION # For memcache busting on new version

RSS_FEED_LIMIT = 15

VULCANIZE = True #PROD

DEFAULT_CACHE_TIME = 600 # seconds

if DEBUG:
  TEMPLATE_CACHE_TIME = 0
else:
  TEMPLATE_CACHE_TIME = 600 # seconds

SEND_EMAIL = False # Flag to turn off email notifications to feature owners.

FIREBASE_SERVER_KEY = os.environ.get('FIREBASE_SERVER_KEY')
