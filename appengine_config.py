from __future__ import division
from __future__ import print_function

import os
import sys
# name of the django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.ext import vendor
vendor.add('lib') # add third party libs to "lib" folder.
