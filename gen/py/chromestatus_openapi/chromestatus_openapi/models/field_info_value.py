from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class FieldInfoValue(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self):  # noqa: E501
        """FieldInfoValue - a model defined in OpenAPI

        """
        self.openapi_types = {
        }

        self.attribute_map = {
        }

    @classmethod
    def from_dict(cls, dikt) -> 'FieldInfoValue':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FieldInfo_value of this FieldInfoValue.  # noqa: E501
        :rtype: FieldInfoValue
        """
        return util.deserialize_model(dikt, cls)
