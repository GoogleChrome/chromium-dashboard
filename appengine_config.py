import os
import sys
import importlib
# name of the django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')

from google.appengine.ext import vendor
vendor.add(lib_path) # add third party libs to "lib" folder.

# Add libraries to pkg_resources working set to find the distribution.
import pkg_resources
pkg_resources.working_set.add_entry(lib_path)
