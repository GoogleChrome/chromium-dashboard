from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class FeatureDictInnerMaturityInfo(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, text=None, short_text=None, val=None):  # noqa: E501
        """FeatureDictInnerMaturityInfo - a model defined in OpenAPI

        :param text: The text of this FeatureDictInnerMaturityInfo.  # noqa: E501
        :type text: str
        :param short_text: The short_text of this FeatureDictInnerMaturityInfo.  # noqa: E501
        :type short_text: str
        :param val: The val of this FeatureDictInnerMaturityInfo.  # noqa: E501
        :type val: int
        """
        self.openapi_types = {
            'text': str,
            'short_text': str,
            'val': int
        }

        self.attribute_map = {
            'text': 'text',
            'short_text': 'short_text',
            'val': 'val'
        }

        self._text = text
        self._short_text = short_text
        self._val = val

    @classmethod
    def from_dict(cls, dikt) -> 'FeatureDictInnerMaturityInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FeatureDictInnerMaturityInfo of this FeatureDictInnerMaturityInfo.  # noqa: E501
        :rtype: FeatureDictInnerMaturityInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def text(self) -> str:
        """Gets the text of this FeatureDictInnerMaturityInfo.


        :return: The text of this FeatureDictInnerMaturityInfo.
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, text: str):
        """Sets the text of this FeatureDictInnerMaturityInfo.


        :param text: The text of this FeatureDictInnerMaturityInfo.
        :type text: str
        """

        self._text = text

    @property
    def short_text(self) -> str:
        """Gets the short_text of this FeatureDictInnerMaturityInfo.


        :return: The short_text of this FeatureDictInnerMaturityInfo.
        :rtype: str
        """
        return self._short_text

    @short_text.setter
    def short_text(self, short_text: str):
        """Sets the short_text of this FeatureDictInnerMaturityInfo.


        :param short_text: The short_text of this FeatureDictInnerMaturityInfo.
        :type short_text: str
        """

        self._short_text = short_text

    @property
    def val(self) -> int:
        """Gets the val of this FeatureDictInnerMaturityInfo.


        :return: The val of this FeatureDictInnerMaturityInfo.
        :rtype: int
        """
        return self._val

    @val.setter
    def val(self, val: int):
        """Sets the val of this FeatureDictInnerMaturityInfo.


        :param val: The val of this FeatureDictInnerMaturityInfo.
        :type val: int
        """

        self._val = val
