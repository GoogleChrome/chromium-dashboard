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
from typing import Any, Optional
from ghapi.core import GhApi
from urllib.error import HTTPError
from urllib.parse import urlparse
import base64
import validators
import html
from framework import secrets


github_crediential = None
github_api_client = None

LINK_TYPE_CHROMIUM_BUG = 'chromium_bug'
LINK_TYPE_GITHUB_ISSUE = 'github_issue'
LINK_TYPE_GITHUB_MARKDOWN = 'github_markdown'
LINK_TYPE_GITHUB_PULL_REQUEST = 'github_pull_request'
LINK_TYPE_MDN_DOCS = 'mdn_docs'
LINK_TYPE_GOOGLE_DOCS = 'google_docs'
LINK_TYPE_MOZILLA_BUG = 'mozilla_bug'
LINK_TYPE_WEBKIT_BUG = 'webkit_bug'
LINK_TYPE_SPECS = 'specs'
LINK_TYPE_WEB = 'web'
LINK_TYPES_REGEX = {
    # https://bugs.chromium.org/p/chromium/issues/detail?id=
    # https://crbug.com/
    # https://code.google.com/p/chromium/issues/detail?id=
    LINK_TYPE_CHROMIUM_BUG: re.compile(r'https?://bugs\.chromium\.org/p/chromium/issues/detail\?id=\d+|https?://crbug\.com/\d+|https?://code\.google\.com/p/chromium/issues/detail\?id=\d+'),
    # https://github.com/GoogleChrome/chromium-dashboard/issues/999
    LINK_TYPE_GITHUB_ISSUE: re.compile(r'https?://(www\.)?github\.com/.*issues/\d+'),
    # https://github.com/GoogleChrome/chromium-dashboard/pull/3044
    LINK_TYPE_GITHUB_PULL_REQUEST: re.compile(r'https?://(www\.)?github\.com/.*pull/\d+'),
    # https://github.com/w3c/reporting/blob/master/EXPLAINER.md
    LINK_TYPE_GITHUB_MARKDOWN: re.compile(r'https?://(www\.)?github\.com/.*\.md.*'),
    # https://developer.mozilla.org/en-US/docs/Web/API/DOMException
    LINK_TYPE_MDN_DOCS: re.compile(r'https?://(www\.)?developer\.mozilla\.org/.*'),
    # https://docs.google.com/document/d/1-M_o-il38aW64Gyk4R23Yaxy1p2Uy7D0i6J5qTWzypU
    LINK_TYPE_GOOGLE_DOCS: re.compile(r'https?://docs\.google\.com/(document|spreadsheets|presentation|forms)/.*'),
    # https://bugzilla.mozilla.org/show_bug.cgi?id=1314686
    LINK_TYPE_MOZILLA_BUG: re.compile(r'https?://bugzilla\.mozilla\.org/show_bug\.cgi\?id=\d+'),
    # https://bugs.webkit.org/show_bug.cgi?id=128456
    LINK_TYPE_WEBKIT_BUG: re.compile(r'https?://bugs\.webkit\.org/show_bug\.cgi\?id=\d+'),
    # https://w3c.github.io/
    # https://w3.org/
    # https://drafts.csswg.org/
    # https://whatwg.org/
    # https://wicg.github.io/
    LINK_TYPE_SPECS: re.compile(r'https?://w3c\.github\.io/.*|https?://[a-z]+\.?w3\.org/.*|https?://drafts\.csswg\.org/.*|https?://[a-z\.]*whatwg\.org/.*|https?://wicg\.github\.io/.*'),
    LINK_TYPE_WEB: re.compile(r'https?://.*'),
}

TAG_REVIEW_URL_PATTERN = re.compile(r'github.com/w3ctag/design-reviews/', re.IGNORECASE)
GECKO_REVIEW_URL_PATTERN = re.compile(
  r'github.com/mozilla/standards-positions/', re.IGNORECASE
)
WEBKIT_REVIEW_URL_PATTERN = re.compile(
  r'github.com/WebKit/standards-positions/', re.IGNORECASE
)

URL_REGEX = re.compile(r'(https?://\S+)')

TIMEOUT = 30  # We wait at most 30 seconds for each web page request.


def valid_url(url):
  try:
    return validators.url(url, public=True)
  except:
    return False


def get_github_api_client():
  """Set up the GitHub client."""
  global github_credential
  global github_api_client
  if github_api_client is None:
    github_credential = secrets.ApiCredential.get_github_credendial()
    github_api_client = GhApi(token=github_credential.token)

  return github_api_client


def rotate_github_client():
  """Try a different github client, e.g., after quota is used up."""
  global github_api_client
  github_credential.record_failure()
  github_api_client = None  # A new one will be selected on when needed.


class Link():

  @classmethod
  def extract_urls_from_value(cls, value: Any) -> list[str]:
    """Extract the urls from the given value."""
    if isinstance(value, str):
      urls = URL_REGEX.findall(value)

      # remove trailing punctuation
      # punctuation similar to string.punctuation except that it does not include "/"
      # this keep url ending with "/"
      punctuation = r"""!"#$%&'()*+,-.:;<=>?@[\]^_`{|}~"""
      urls = [url.rstrip(punctuation) for url in urls]
    elif isinstance(value, list):
      urls = [url for url in value if isinstance(url, str) and URL_REGEX.match(url)]
    else:
      urls = []
    return [url for url in urls if valid_url(url)]

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
    self.http_error_code: Optional[int] = None
    self.information = None
    logging.info(f'Constructed Link for {url} with type {self.type}')

  def _fetch_github_file(
          self, owner: str, repo: str, ref: str, file_path: str,
          retries=1):
    """Get a file from GitHub."""
    client = get_github_api_client()
    try:
      # try to get the branch information, if it exists, update branch name
      # this handles the case where the branch is renamed.
      branch_information = client.repos.get_branch(
          owner=owner, repo=repo, branch=ref)
      ref = branch_information.name
    except HTTPError as e:
      # if the branch does not exist, then it is probably a commit hash
      if e.code != 404:
        raise e

    try:
      information = client.repos.get_content(
          owner=owner, repo=repo, path=file_path, ref=ref)
      return information
    except HTTPError as e:
      logging.info(f'Got http response code {e.code}')
      if e.code != 404 and retries > 0:
        rotate_github_client()
        return self._fetch_github_file(
            owner, repo, ref, file_path, retries=retries - 1)
      else:
        raise e

  def _parse_github_markdown(self) -> dict[str, object]:
    parsed_url = urlparse(self.url)
    path = parsed_url.path
    owner = path.split('/')[1]
    repo = path.split('/')[2]
    ref = path.split('/')[4]
    file_path = '/'.join(path.split('/')[5:])

    information = self._fetch_github_file(owner, repo, ref, file_path)

    # decode the content from base64
    content_str = information.content
    content_decoded = base64.b64decode(content_str).decode('utf-8')
    # get markdown title, remove beginning and trailing # but keep the rest
    title = content_decoded.split('\n')[0].strip('#').strip()
    information['_parsed_title'] = title

    return information

  def _fetch_github_issue(
          self, owner: str, repo: str, issue_id: int,
          retries=1) -> dict[str, Any]:
    """Get an issue from GitHub."""
    try:
      client = get_github_api_client()
      resp = client.issues.get(owner=owner, repo=repo, issue_number=issue_id)
      return resp
    except HTTPError as e:
      logging.info(f'Got http response code {e.code}')
      if e.code != 404 and retries > 0:
        rotate_github_client()
        return self._fetch_github_issue(
            owner, repo, issue_id, retries=retries - 1)
      else:
        raise e

  def _parse_github_issue(self) -> dict[str, str | None]:
    """Parse the information from the github issue tracker."""

    parsed_url = urlparse(self.url)
    path = parsed_url.path
    owner = path.split('/')[1]
    repo = path.split('/')[2]
    issue_id = path.split('/')[4]

    resp = self._fetch_github_issue(owner, repo, int(issue_id))
    information = {
        'url': resp.get('url'),
        'number': resp.get('number'),
        'title': resp.get('title'),
        'user_login': (
            resp['user'].get('login') if resp.get('user') else None),
        'state': resp.get('state'),
        'state_reason': resp.get('state_reason'),
        'assignee_login': (
            resp['assignee'].get('login') if resp.get('assignee') else None),
        'created_at': resp.get('created_at'),
        'updated_at': resp.get('updated_at'),
        'closed_at': resp.get('closed_at'),
        'labels': [label.get('name') for label in resp.get('labels', [])],
    }

    return information

  def _parse_chromium_bug(self) -> dict[str, object]:
    """Parse the information from the chromium bug tracker."""

    endpoint = 'https://bugs.chromium.org/prpc/monorail.Issues/GetIssue'

    parsed_url = urlparse(self.url)
    if parsed_url.netloc == 'bugs.chromium.org':
      issue_id = parsed_url.query.split('id=')[-1].split('&')[0]
    elif parsed_url.netloc == 'crbug.com':
      issue_id = parsed_url.path.lstrip('/')
    elif parsed_url.netloc == 'code.google.com':
      issue_id = parsed_url.query.split('id=')[-1].split('&')[0]

    # csrf token is required, its expiration is about 2 hours according to the tokenExpiresSec field
    # technically, we could cache the csrf token and reuse it for 2 hours
    # TODO: consider using a monorail API client with OAuth

    csrf_response = requests.get(
        "https://bugs.chromium.org/p/chromium/issues/wizard", timeout=TIMEOUT)
    csrf_token = re.findall("'token': '(.*?)'", csrf_response.text)
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

    bug_response = requests.post(
        endpoint, json=body, headers=headers, timeout=TIMEOUT)
    json_str = bug_response.text

    # remove )]}' from the beginning of the response
    if json_str.startswith(")]}'"):
      json_str = json_str[5:]

    information: dict[str, Any] = json.loads(json_str)

    return information.get('issue', None)

  def _parse_html_head(self):
    response = requests.get(self.url, timeout=TIMEOUT)
    # unescape html, e.g. &amp; -> &
    html_str = html.unescape(response.text)

    title = re.search(r'<title>(.*?)</title>', html_str)
    # use \s+ instead of whitespace, to match multiple whitespaces or newlines
    title_og = re.search(r'<meta property="og:title"\s+content="(.*?)"', html_str)
    description = re.search(r'<meta name="description"\s+content="(.*?)"', html_str)
    description_og = re.search(r'<meta property="og:description"\s+content="(.*?)"', html_str)

    return {
        'title': title_og.group(1) if title_og else (title.group(1) if title else None),
        'description': description_og.group(1) if description_og else (description.group(1) if description else None),
    }

  def _validate_url(self) -> bool:
    """The `_validate_url` method is used to validate the URL associated with the Link object. It
    sends a GET request to the URL and checks the response status code. If the status code is not
    200 (OK), it sets the `is_error` flag to True and stores the HTTP error code. This method is
    used to determine if the URL is accessible and valid."""
    res = requests.get(self.url, allow_redirects=True, timeout=TIMEOUT)
    if res.status_code != 200:
      self.is_error = True
      self.http_error_code = res.status_code
      return False
    return True

  def parse(self):
    """Parse the link and store the information."""
    # Flush logs because GAE instances killed for exceeding request time limit
    # may lose logging output that has not been flushed.
    logging.getLogger().handlers[0].flush()

    try:
      if not self.type or not self._validate_url():
        # if the link is not valid, return early
        self.is_parsed = True
        return

      # TODO(jrobbins): Re-enable after issues.chromium.org has an API
      # if self.type == LINK_TYPE_CHROMIUM_BUG:
      #  self.information = self._parse_chromium_bug()

      if self.type == LINK_TYPE_GITHUB_ISSUE:
        self.information = self._parse_github_issue()
      elif self.type == LINK_TYPE_GITHUB_PULL_REQUEST:
        # we can also use github issue api to get pull request information
        # pull request api can get more information but we don't need it for now
        self.information = self._parse_github_issue()
      elif self.type == LINK_TYPE_GITHUB_MARKDOWN:
        self.information = self._parse_github_markdown()
      elif self.type in [
          LINK_TYPE_MDN_DOCS,
          LINK_TYPE_GOOGLE_DOCS,
          LINK_TYPE_MOZILLA_BUG,
          LINK_TYPE_WEBKIT_BUG,
          LINK_TYPE_SPECS,
      ]:
        self.information = self._parse_html_head()
      elif self.type == LINK_TYPE_WEB:
        self.information = None
    except Exception as e:
      logging.error(f'Error parsing {self.type} {self.url}: {e}')
      self.error = e
      self.is_error = True
      if isinstance(e, HTTPError):
        self.http_error_code = e.code
      self.information = None
    self.is_parsed = True
