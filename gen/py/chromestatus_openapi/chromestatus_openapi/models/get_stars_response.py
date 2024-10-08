from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class GetStarsResponse(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, feature_ids=None):  # noqa: E501
        """GetStarsResponse - a model defined in OpenAPI

        :param feature_ids: The feature_ids of this GetStarsResponse.  # noqa: E501
        :type feature_ids: List[int]
        """
        self.openapi_types = {
            'feature_ids': List[int]
        }

        self.attribute_map = {
            'feature_ids': 'feature_ids'
        }

        self._feature_ids = feature_ids

    @classmethod
    def from_dict(cls, dikt) -> 'GetStarsResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The GetStarsResponse of this GetStarsResponse.  # noqa: E501
        :rtype: GetStarsResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def feature_ids(self) -> List[int]:
        """Gets the feature_ids of this GetStarsResponse.


        :return: The feature_ids of this GetStarsResponse.
        :rtype: List[int]
        """
        return self._feature_ids

    @feature_ids.setter
    def feature_ids(self, feature_ids: List[int]):
        """Sets the feature_ids of this GetStarsResponse.


        :param feature_ids: The feature_ids of this GetStarsResponse.
        :type feature_ids: List[int]
        """

        self._feature_ids = feature_ids
