# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from __future__ import print_function

import datetime
import os

# We cannot import settings.py because it imports this file.
DEV_MODE = os.environ['SERVER_SOFTWARE'].startswith('Development')
UNIT_TEST_MODE = os.environ['SERVER_SOFTWARE'].startswith('test')


def _log(severity, format_str, args):
  message = format_str % args
  if DEV_MODE or UNIT_TEST_MODE:
    now = datetime.datetime.now()
    timestr = now.strftime('%Y-%m-%d %H:%M:%S')
    milli = int(now.microsecond / 1000)
    line = '%-8s %s,%03d: %s' % (severity, timestr, milli, message)
    print(line)
  else:
    # AppEngine adds the data and time automatically.
    # Severity is always Error, but we don't care.
    print(message)


def debug(format_str, *args):
  _log('DEBUG', format_str, args)


def info(format_str, *args):
  _log('INFO', format_str, args)


def warning(format_str, *args):
  _log('WARMING', format_str, args)


def error(format_str, *args):
  _log('ERROR', format_str, args)


def critical(format_str, *args):
  _log('CRITICAL', format_str, args)

# Note: we do not support logging.exception().
