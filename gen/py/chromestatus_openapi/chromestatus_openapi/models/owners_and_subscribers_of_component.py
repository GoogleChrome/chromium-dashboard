from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class OwnersAndSubscribersOfComponent(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None, name=None, subscriber_ids=None, owner_ids=None):  # noqa: E501
        """OwnersAndSubscribersOfComponent - a model defined in OpenAPI

        :param id: The id of this OwnersAndSubscribersOfComponent.  # noqa: E501
        :type id: str
        :param name: The name of this OwnersAndSubscribersOfComponent.  # noqa: E501
        :type name: str
        :param subscriber_ids: The subscriber_ids of this OwnersAndSubscribersOfComponent.  # noqa: E501
        :type subscriber_ids: List[int]
        :param owner_ids: The owner_ids of this OwnersAndSubscribersOfComponent.  # noqa: E501
        :type owner_ids: List[int]
        """
        self.openapi_types = {
            'id': str,
            'name': str,
            'subscriber_ids': List[int],
            'owner_ids': List[int]
        }

        self.attribute_map = {
            'id': 'id',
            'name': 'name',
            'subscriber_ids': 'subscriber_ids',
            'owner_ids': 'owner_ids'
        }

        self._id = id
        self._name = name
        self._subscriber_ids = subscriber_ids
        self._owner_ids = owner_ids

    @classmethod
    def from_dict(cls, dikt) -> 'OwnersAndSubscribersOfComponent':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The OwnersAndSubscribersOfComponent of this OwnersAndSubscribersOfComponent.  # noqa: E501
        :rtype: OwnersAndSubscribersOfComponent
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> str:
        """Gets the id of this OwnersAndSubscribersOfComponent.


        :return: The id of this OwnersAndSubscribersOfComponent.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this OwnersAndSubscribersOfComponent.


        :param id: The id of this OwnersAndSubscribersOfComponent.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")  # noqa: E501

        self._id = id

    @property
    def name(self) -> str:
        """Gets the name of this OwnersAndSubscribersOfComponent.


        :return: The name of this OwnersAndSubscribersOfComponent.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this OwnersAndSubscribersOfComponent.


        :param name: The name of this OwnersAndSubscribersOfComponent.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def subscriber_ids(self) -> List[int]:
        """Gets the subscriber_ids of this OwnersAndSubscribersOfComponent.


        :return: The subscriber_ids of this OwnersAndSubscribersOfComponent.
        :rtype: List[int]
        """
        return self._subscriber_ids

    @subscriber_ids.setter
    def subscriber_ids(self, subscriber_ids: List[int]):
        """Sets the subscriber_ids of this OwnersAndSubscribersOfComponent.


        :param subscriber_ids: The subscriber_ids of this OwnersAndSubscribersOfComponent.
        :type subscriber_ids: List[int]
        """

        self._subscriber_ids = subscriber_ids

    @property
    def owner_ids(self) -> List[int]:
        """Gets the owner_ids of this OwnersAndSubscribersOfComponent.


        :return: The owner_ids of this OwnersAndSubscribersOfComponent.
        :rtype: List[int]
        """
        return self._owner_ids

    @owner_ids.setter
    def owner_ids(self, owner_ids: List[int]):
        """Sets the owner_ids of this OwnersAndSubscribersOfComponent.


        :param owner_ids: The owner_ids of this OwnersAndSubscribersOfComponent.
        :type owner_ids: List[int]
        """

        self._owner_ids = owner_ids
