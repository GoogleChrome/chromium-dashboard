from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi.models.activity import Activity
from chromestatus_openapi import util

from chromestatus_openapi.models.activity import Activity  # noqa: E501

class GetCommentsResponse(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, comments=None):  # noqa: E501
        """GetCommentsResponse - a model defined in OpenAPI

        :param comments: The comments of this GetCommentsResponse.  # noqa: E501
        :type comments: List[Activity]
        """
        self.openapi_types = {
            'comments': List[Activity]
        }

        self.attribute_map = {
            'comments': 'comments'
        }

        self._comments = comments

    @classmethod
    def from_dict(cls, dikt) -> 'GetCommentsResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The GetCommentsResponse of this GetCommentsResponse.  # noqa: E501
        :rtype: GetCommentsResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def comments(self) -> List[Activity]:
        """Gets the comments of this GetCommentsResponse.


        :return: The comments of this GetCommentsResponse.
        :rtype: List[Activity]
        """
        return self._comments

    @comments.setter
    def comments(self, comments: List[Activity]):
        """Sets the comments of this GetCommentsResponse.


        :param comments: The comments of this GetCommentsResponse.
        :type comments: List[Activity]
        """

        self._comments = comments
