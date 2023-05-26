import re
import requests
import json
import logging
LINK_TYPE_CHROMIUM_BUG = 'chromium_bug'
LINK_TYPE_UNKNOWN = 'unknown'
LINK_TYPES_REGEX = {
    # https://bugs.chromium.org/p/chromium/issues/detail?id=
    LINK_TYPE_CHROMIUM_BUG: re.compile(r'https://bugs\.chromium\.org/p/chromium/issues/detail\?.*'),
    # any other links
    LINK_TYPE_UNKNOWN: re.compile(r'https?://.*'),
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

    def _parse_chromium_bug(self) -> dict:
        """Parse the information from the chromium bug tracker."""

        endpoint = 'https://bugs.chromium.org/prpc/monorail.Issues/GetIssue'

        issue_id = self.url.split('id=')[-1]

        # csrf token is required, its expiration is about 2 hours according to the tokenExpiresSec field
        # technically, we could cache the csrf token and reuse it for 2 hours

        csrf_token = re.findall(
            "'token': '(.*?)'", requests.get("https://bugs.chromium.org/p/chromium/issues/wizard").text)
        csrf_token = csrf_token[0] if csrf_token else None

        if csrf_token is None:
            raise Exception("Could not find bugs.chromium.org CSRF token")

        headers = {
            'accept': 'application/json',
            'x-xsrf-token': csrf_token,
            'content-type': 'application/json',
        }
        body = {
            'issueRef': {
                'projectName': 'chromium',
                'localId': int(issue_id)
            },
        }

        information = requests.post(endpoint, json=body, headers=headers).text

        # remove )]}' from the beginning of the response
        if information.startswith(")]}'"):
            information = information[5:]

        information = json.loads(information)

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
        elif self.type == LINK_TYPE_UNKNOWN:
            # TODO: parse other url title and description, og tags, etc.
            self.information = None
        self.is_parsed = True
