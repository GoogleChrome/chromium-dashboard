import os

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

################################################################################

if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
    os.getenv('SETTINGS_MODE') == 'prod'):
  PROD = True
else:
  PROD = False

DEBUG = not PROD
TEMPLATE_DEBUG = DEBUG

APP_TITLE = 'Chrome Platform Status'

SECRET_KEY = os.environ['DJANGO_SECRET']

APP_VERSION = os.environ['CURRENT_VERSION_ID'].split('.')[0]
MEMCACHE_KEY_PREFIX = APP_VERSION # For memcache busting on new version

RSS_FEED_LIMIT = 15

VULCANIZE = True #PROD

DEFAULT_CACHE_TIME = 600 # seconds

USE_I18N = False

if DEBUG:
  TEMPLATE_CACHE_TIME = 0
else:
  TEMPLATE_CACHE_TIME = 600 # seconds

SEND_EMAIL = PROD # Flag to turn off email notifications to feature owners.
SEND_PUSH_NOTIFICATIONS = PROD # Flag to turn off sending push notifications for all users.

FIREBASE_SERVER_KEY = os.environ.get('FIREBASE_SERVER_KEY')
