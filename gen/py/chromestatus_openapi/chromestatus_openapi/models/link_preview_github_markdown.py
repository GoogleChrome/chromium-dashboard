from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi.models.link_preview_github_markdown_all_of_information import LinkPreviewGithubMarkdownAllOfInformation
from chromestatus_openapi import util

from chromestatus_openapi.models.link_preview_github_markdown_all_of_information import LinkPreviewGithubMarkdownAllOfInformation  # noqa: E501

class LinkPreviewGithubMarkdown(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, url=None, type=None, information=None, http_error_code=None):  # noqa: E501
        """LinkPreviewGithubMarkdown - a model defined in OpenAPI

        :param url: The url of this LinkPreviewGithubMarkdown.  # noqa: E501
        :type url: str
        :param type: The type of this LinkPreviewGithubMarkdown.  # noqa: E501
        :type type: str
        :param information: The information of this LinkPreviewGithubMarkdown.  # noqa: E501
        :type information: LinkPreviewGithubMarkdownAllOfInformation
        :param http_error_code: The http_error_code of this LinkPreviewGithubMarkdown.  # noqa: E501
        :type http_error_code: int
        """
        self.openapi_types = {
            'url': str,
            'type': str,
            'information': LinkPreviewGithubMarkdownAllOfInformation,
            'http_error_code': int
        }

        self.attribute_map = {
            'url': 'url',
            'type': 'type',
            'information': 'information',
            'http_error_code': 'http_error_code'
        }

        self._url = url
        self._type = type
        self._information = information
        self._http_error_code = http_error_code

    @classmethod
    def from_dict(cls, dikt) -> 'LinkPreviewGithubMarkdown':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The LinkPreviewGithubMarkdown of this LinkPreviewGithubMarkdown.  # noqa: E501
        :rtype: LinkPreviewGithubMarkdown
        """
        return util.deserialize_model(dikt, cls)

    @property
    def url(self) -> str:
        """Gets the url of this LinkPreviewGithubMarkdown.


        :return: The url of this LinkPreviewGithubMarkdown.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url: str):
        """Sets the url of this LinkPreviewGithubMarkdown.


        :param url: The url of this LinkPreviewGithubMarkdown.
        :type url: str
        """
        if url is None:
            raise ValueError("Invalid value for `url`, must not be `None`")  # noqa: E501

        self._url = url

    @property
    def type(self) -> str:
        """Gets the type of this LinkPreviewGithubMarkdown.


        :return: The type of this LinkPreviewGithubMarkdown.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this LinkPreviewGithubMarkdown.


        :param type: The type of this LinkPreviewGithubMarkdown.
        :type type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501

        self._type = type

    @property
    def information(self) -> LinkPreviewGithubMarkdownAllOfInformation:
        """Gets the information of this LinkPreviewGithubMarkdown.


        :return: The information of this LinkPreviewGithubMarkdown.
        :rtype: LinkPreviewGithubMarkdownAllOfInformation
        """
        return self._information

    @information.setter
    def information(self, information: LinkPreviewGithubMarkdownAllOfInformation):
        """Sets the information of this LinkPreviewGithubMarkdown.


        :param information: The information of this LinkPreviewGithubMarkdown.
        :type information: LinkPreviewGithubMarkdownAllOfInformation
        """
        if information is None:
            raise ValueError("Invalid value for `information`, must not be `None`")  # noqa: E501

        self._information = information

    @property
    def http_error_code(self) -> int:
        """Gets the http_error_code of this LinkPreviewGithubMarkdown.


        :return: The http_error_code of this LinkPreviewGithubMarkdown.
        :rtype: int
        """
        return self._http_error_code

    @http_error_code.setter
    def http_error_code(self, http_error_code: int):
        """Sets the http_error_code of this LinkPreviewGithubMarkdown.


        :param http_error_code: The http_error_code of this LinkPreviewGithubMarkdown.
        :type http_error_code: int
        """

        self._http_error_code = http_error_code
