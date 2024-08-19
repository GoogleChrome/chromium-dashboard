from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class PostStarsRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, feature_id=None, starred=True):  # noqa: E501
        """PostStarsRequest - a model defined in OpenAPI

        :param feature_id: The feature_id of this PostStarsRequest.  # noqa: E501
        :type feature_id: int
        :param starred: The starred of this PostStarsRequest.  # noqa: E501
        :type starred: bool
        """
        self.openapi_types = {
            'feature_id': int,
            'starred': bool
        }

        self.attribute_map = {
            'feature_id': 'featureId',
            'starred': 'starred'
        }

        self._feature_id = feature_id
        self._starred = starred

    @classmethod
    def from_dict(cls, dikt) -> 'PostStarsRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The PostStarsRequest of this PostStarsRequest.  # noqa: E501
        :rtype: PostStarsRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def feature_id(self) -> int:
        """Gets the feature_id of this PostStarsRequest.


        :return: The feature_id of this PostStarsRequest.
        :rtype: int
        """
        return self._feature_id

    @feature_id.setter
    def feature_id(self, feature_id: int):
        """Sets the feature_id of this PostStarsRequest.


        :param feature_id: The feature_id of this PostStarsRequest.
        :type feature_id: int
        """
        if feature_id is None:
            raise ValueError("Invalid value for `feature_id`, must not be `None`")  # noqa: E501

        self._feature_id = feature_id

    @property
    def starred(self) -> bool:
        """Gets the starred of this PostStarsRequest.


        :return: The starred of this PostStarsRequest.
        :rtype: bool
        """
        return self._starred

    @starred.setter
    def starred(self, starred: bool):
        """Sets the starred of this PostStarsRequest.


        :param starred: The starred of this PostStarsRequest.
        :type starred: bool
        """

        self._starred = starred
