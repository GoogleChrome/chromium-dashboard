import os
import sys
import importlib
# name of the django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Add libraries to pkg_resources working set to find the distribution.
import pkg_resources
pkg_resources.working_set.add_entry(lib_path)
