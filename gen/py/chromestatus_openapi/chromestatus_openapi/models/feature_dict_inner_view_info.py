from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class FeatureDictInnerViewInfo(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, text=None, val=None, url=None, notes=None):  # noqa: E501
        """FeatureDictInnerViewInfo - a model defined in OpenAPI

        :param text: The text of this FeatureDictInnerViewInfo.  # noqa: E501
        :type text: str
        :param val: The val of this FeatureDictInnerViewInfo.  # noqa: E501
        :type val: int
        :param url: The url of this FeatureDictInnerViewInfo.  # noqa: E501
        :type url: str
        :param notes: The notes of this FeatureDictInnerViewInfo.  # noqa: E501
        :type notes: str
        """
        self.openapi_types = {
            'text': str,
            'val': int,
            'url': str,
            'notes': str
        }

        self.attribute_map = {
            'text': 'text',
            'val': 'val',
            'url': 'url',
            'notes': 'notes'
        }

        self._text = text
        self._val = val
        self._url = url
        self._notes = notes

    @classmethod
    def from_dict(cls, dikt) -> 'FeatureDictInnerViewInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FeatureDictInnerViewInfo of this FeatureDictInnerViewInfo.  # noqa: E501
        :rtype: FeatureDictInnerViewInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def text(self) -> str:
        """Gets the text of this FeatureDictInnerViewInfo.


        :return: The text of this FeatureDictInnerViewInfo.
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, text: str):
        """Sets the text of this FeatureDictInnerViewInfo.


        :param text: The text of this FeatureDictInnerViewInfo.
        :type text: str
        """

        self._text = text

    @property
    def val(self) -> int:
        """Gets the val of this FeatureDictInnerViewInfo.


        :return: The val of this FeatureDictInnerViewInfo.
        :rtype: int
        """
        return self._val

    @val.setter
    def val(self, val: int):
        """Sets the val of this FeatureDictInnerViewInfo.


        :param val: The val of this FeatureDictInnerViewInfo.
        :type val: int
        """

        self._val = val

    @property
    def url(self) -> str:
        """Gets the url of this FeatureDictInnerViewInfo.


        :return: The url of this FeatureDictInnerViewInfo.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url: str):
        """Sets the url of this FeatureDictInnerViewInfo.


        :param url: The url of this FeatureDictInnerViewInfo.
        :type url: str
        """

        self._url = url

    @property
    def notes(self) -> str:
        """Gets the notes of this FeatureDictInnerViewInfo.


        :return: The notes of this FeatureDictInnerViewInfo.
        :rtype: str
        """
        return self._notes

    @notes.setter
    def notes(self, notes: str):
        """Sets the notes of this FeatureDictInnerViewInfo.


        :param notes: The notes of this FeatureDictInnerViewInfo.
        :type notes: str
        """

        self._notes = notes
