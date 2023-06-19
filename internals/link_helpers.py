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
from ghapi.core import GhApi
from urllib.error import HTTPError
from urllib.parse import urlparse
import base64

github_api_client = GhApi()

LINK_TYPE_CHROMIUM_BUG = 'chromium_bug'
LINK_TYPE_GITHUB_ISSUE = 'github_issue'
LINK_TYPE_GITHUB_MARKDOWN = 'github_markdown'
LINK_TYPE_WEB = 'web'
LINK_TYPES_REGEX = {
    # https://bugs.chromium.org/p/chromium/issues/detail?id=
    LINK_TYPE_CHROMIUM_BUG: re.compile(r'https://bugs\.chromium\.org/p/chromium/issues/detail\?.*'),
    LINK_TYPE_GITHUB_ISSUE: re.compile(r'https://(www\.)?github\.com/.*issues/\d+'),
    LINK_TYPE_GITHUB_MARKDOWN: re.compile(r'https://(www\.)?github\.com/.*\.md.*'),
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

  def _parse_github_markdown(self) -> dict[str, object]:
    parsed_url = urlparse(self.url)
    path = parsed_url.path
    owner = path.split('/')[1]
    repo = path.split('/')[2]
    ref = path.split('/')[4]
    file_path = '/'.join(path.split('/')[5:])
    try:
      # try to get the branch information, if it exists, update branch name
      # this handles the case where the branch is renamed
      branch_information = github_api_client.repos.get_branch(
          owner=owner, repo=repo, branch=ref)
      ref = branch_information.name
    except HTTPError as e:
      # if the branch does not exist, then it is probably a commit hash
      if e.code != 404:
        raise e

    information = github_api_client.repos.get_content(
        owner=owner, repo=repo, path=file_path, ref=ref)

    # decode the content from base64
    content_str = information.content
    content_decoded = base64.b64decode(content_str).decode('utf-8')
    # get markdown title, remove beginning and trailing # but keep the rest
    title = content_decoded.split('\n')[0].strip('#').strip()
    information['_parsed_title'] = title

    return information

  def _parse_github_issue(self) -> dict[str, object]:
    """Parse the information from the github issue tracker."""

    parsed_url = urlparse(self.url)
    path = parsed_url.path
    owner = path.split('/')[1]
    repo = path.split('/')[2]
    issue_id = path.split('/')[4]

    information = github_api_client.issues.get(
        owner=owner, repo=repo, issue_number=int(issue_id))

    return information

  def _parse_chromium_bug(self) -> dict[str, object]:
    """Parse the information from the chromium bug tracker."""

    endpoint = 'https://bugs.chromium.org/prpc/monorail.Issues/GetIssue'

    parsed_url = urlparse(self.url)
    issue_id = parsed_url.query.split('id=')[-1].split('&')[0]

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
    try:
      if self.type == LINK_TYPE_CHROMIUM_BUG:
        self.information = self._parse_chromium_bug()
      elif self.type == LINK_TYPE_GITHUB_ISSUE:
        self.information = self._parse_github_issue()
      elif self.type == LINK_TYPE_GITHUB_MARKDOWN:
        self.information = self._parse_github_markdown()
      elif self.type == LINK_TYPE_WEB:
        # TODO: parse other url title and description, og tags, etc.
        self.information = None
    except Exception as e:
      logging.error(f'Error parsing {self.type} {self.url}: {e}')
      self.error = e
      self.is_error = True
      self.information = None
    self.is_parsed = True
