import os
# name of the django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.ext import vendor
vendor.add('lib') # add third party libs to "lib" folder.
