# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

import re
import requests
import json
import logging
from typing import Any

LINK_TYPE_CHROMIUM_BUG = 'chromium_bug'
LINK_TYPE_WEB = 'web'
LINK_TYPES_REGEX = {
    # https://bugs.chromium.org/p/chromium/issues/detail?id=
    LINK_TYPE_CHROMIUM_BUG: re.compile(r'https://bugs\.chromium\.org/p/chromium/issues/detail\?.*'),
    # any other links
    LINK_TYPE_WEB: re.compile(r'https?://.*'),
}


class Link():

  @classmethod
  def get_type(cls, link: str) -> str | None:
    """Return Link_Type if the given link is valid. Otherwise, return None."""
    for link_type, regex in LINK_TYPES_REGEX.items():
      if regex.match(link):
        return link_type
    return None

  def __init__(self, url: str):
    self.url = url
    self.type = Link.get_type(url)
    self.is_parsed = False
    self.is_error = False
    self.information = None

  def _parse_chromium_bug(self) -> dict[str, object]:
    """Parse the information from the chromium bug tracker."""

    endpoint = 'https://bugs.chromium.org/prpc/monorail.Issues/GetIssue'

    issue_id = self.url.split('id=')[-1]

    # csrf token is required, its expiration is about 2 hours according to the tokenExpiresSec field
    # technically, we could cache the csrf token and reuse it for 2 hours
    # TODO: consider using a monorail API client with OAuth
    
    csrf_token = re.findall(
        "'token': '(.*?)'", requests.get("https://bugs.chromium.org/p/chromium/issues/wizard").text)
    csrf_token = csrf_token[0] if csrf_token else None

    if csrf_token is None:
      raise Exception("Could not find bugs.chromium.org CSRF token")

    headers = {
        'accept': 'application/json',
        'x-xsrf-token': str(csrf_token),
        'content-type': 'application/json',
    }
    body = {
        'issueRef': {
            'projectName': 'chromium',
            'localId': int(issue_id)
        },
    }

    json_str = requests.post(endpoint, json=body, headers=headers).text

    # remove )]}' from the beginning of the response
    if json_str.startswith(")]}'"):
      json_str = json_str[5:]

    information: dict[str, Any] = json.loads(json_str)

    return information.get('issue', None)

  def parse(self):
    """Parse the link and store the information."""

    if self.type == LINK_TYPE_CHROMIUM_BUG:
      try:
        self.information = self._parse_chromium_bug()
      except Exception as e:
        logging.error(f'Error parsing chromium bug {self.url}: {e}')
        self.is_error = True
        self.information = None
    elif self.type == LINK_TYPE_WEB:
      # TODO: parse other url title and description, og tags, etc.
      self.information = None
    self.is_parsed = True
