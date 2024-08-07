from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class GetIntentResponse(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, subject=None, email_body=None):  # noqa: E501
        """GetIntentResponse - a model defined in OpenAPI

        :param subject: The subject of this GetIntentResponse.  # noqa: E501
        :type subject: str
        :param email_body: The email_body of this GetIntentResponse.  # noqa: E501
        :type email_body: str
        """
        self.openapi_types = {
            'subject': str,
            'email_body': str
        }

        self.attribute_map = {
            'subject': 'subject',
            'email_body': 'email_body'
        }

        self._subject = subject
        self._email_body = email_body

    @classmethod
    def from_dict(cls, dikt) -> 'GetIntentResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The GetIntentResponse of this GetIntentResponse.  # noqa: E501
        :rtype: GetIntentResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def subject(self) -> str:
        """Gets the subject of this GetIntentResponse.


        :return: The subject of this GetIntentResponse.
        :rtype: str
        """
        return self._subject

    @subject.setter
    def subject(self, subject: str):
        """Sets the subject of this GetIntentResponse.


        :param subject: The subject of this GetIntentResponse.
        :type subject: str
        """
        if subject is None:
            raise ValueError("Invalid value for `subject`, must not be `None`")  # noqa: E501

        self._subject = subject

    @property
    def email_body(self) -> str:
        """Gets the email_body of this GetIntentResponse.


        :return: The email_body of this GetIntentResponse.
        :rtype: str
        """
        return self._email_body

    @email_body.setter
    def email_body(self, email_body: str):
        """Sets the email_body of this GetIntentResponse.


        :param email_body: The email_body of this GetIntentResponse.
        :type email_body: str
        """
        if email_body is None:
            raise ValueError("Invalid value for `email_body`, must not be `None`")  # noqa: E501

        self._email_body = email_body
