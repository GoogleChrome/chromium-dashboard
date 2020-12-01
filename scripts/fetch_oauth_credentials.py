from __future__ import division
from __future__ import print_function

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""OAuth 2.0 Bootstrapper for App Engine dev server development.

Adapted from:
https://code.google.com/p/google-cloud-storage-samples/source/browse/gs-oauth.py
"""

__author__ = ('ericbidelman@chromium.org (Eric Bidelman), '
              'nherring@google.com (Nathan Herring)')


import datetime
import re
import os
import sys
from pkg_resources import parse_version


def downloadUsage(err, downloadUrl=None):
  """Emit usage statement with download information."""
  if downloadUrl is None:
    downloadString = 'Run'
  else:
    downloadString = 'Download available at %s or run' % downloadUrl
  print('%s\n%s%s' % (
      err,
      downloadString,
      ' setup.py on the google-api-python-client:\n' +
      'https://code.google.com/p/google-api-python-client/downloads'))
  sys.exit(1)

def importUsage(lib, downloadUrl=None):
  """Emit a failed import error with download information."""
  downloadUsage('Could not load %s module.' % lib, downloadUrl)

#
# Import boilerplate to make it easy to diagnose when the right modules
# are not installed and how to remedy it.
#

try:
  from gflags import gflags
  print(gflags.FLAGS)
except:
  importUsage('gflags', 'https://code.google.com/p/python-gflags/downloads/')

try:
  import httplib2
except:
  importUsage('httplib2', 'https://code.google.com/p/httplib2/downloads/')

OAUTH2CLIENT_REQUIRED_VERSION = '1.0b8'
try:
  from oauth2client.file import Storage
  from oauth2client.client import flow_from_clientsecrets
  from oauth2client.client import OAuth2WebServerFlow
  from oauth2client.tools import run
  import oauth2client
except:
  importUsage('oauth2client')
oauth2client_version = None
if '__version__' not in oauth2client.__dict__:
  if '__file__' in oauth2client.__dict__:
    verMatch = re.search(r'google_api_python_client-([^-]+)',
                         oauth2client.__dict__['__file__'])
    if verMatch is not None:
      oauth2client_version = verMatch.group(1)
      oauth2client_version = re.sub('beta', 'b', oauth2client_version)
else:
  oauth2client_version = oauth2client.__dict__['__version__']
if oauth2client_version is None:
  downloadUsage('Could not determine version of oauth2client module.\n' +
      'Miminum required version is %s.' % OAUTH2CLIENT_REQUIRED_VERSION)
elif (parse_version(oauth2client_version) <
      parse_version(OAUTH2CLIENT_REQUIRED_VERSION)):
  downloadUsage(('oauth2client module version %s is too old.\n' +
      'Miminum required version is %s.') % (oauth2client_version,
      OAUTH2CLIENT_REQUIRED_VERSION))

#
# End of the import boilerplate
#

FLAGS = gflags.FLAGS

gflags.DEFINE_multistring(
  'scope',
  'https://www.googleapis.com/auth/devstorage.read_only',
  'API scope to use')

gflags.DEFINE_string(
  'client_secrets_file',
  os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
  'File name for client_secrets.json')

gflags.DEFINE_string(
  'credentials_file',
  os.path.join(os.path.dirname(__file__), 'oauth2.data2'),
  'File name for storing OAuth 2.0 credentials.',
  short_name='f')


def main(argv):
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError, e:
    print('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  storage = Storage(FLAGS.credentials_file)
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    print('Acquiring initial credentials...')

    # Need to acquire token using @google.com account.
    flow = flow_from_clientsecrets(
        FLAGS.client_secrets_file,
        scope=' '.join(FLAGS.scope),
        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        message='Error - client_secrets_file not found')

    credentials = run(flow, storage)
  elif credentials.access_token_expired:
    print('Refreshing access token...')
    credentials.refresh(httplib2.Http())

  print('Refresh token:', credentials.refresh_token)
  print('Access token:', credentials.access_token)
  delta = credentials.token_expiry - datetime.datetime.utcnow()
  print('Access token expires: %sZ (%dm %ds)' % (credentials.token_expiry,
      delta.seconds / 60, delta.seconds % 60))


if __name__ == '__main__':
  main(sys.argv)
