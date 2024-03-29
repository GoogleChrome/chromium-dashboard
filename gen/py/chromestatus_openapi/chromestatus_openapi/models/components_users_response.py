from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi.models.components_user import ComponentsUser
from chromestatus_openapi.models.owners_and_subscribers_of_component import OwnersAndSubscribersOfComponent
from chromestatus_openapi import util

from chromestatus_openapi.models.components_user import ComponentsUser  # noqa: E501
from chromestatus_openapi.models.owners_and_subscribers_of_component import OwnersAndSubscribersOfComponent  # noqa: E501

class ComponentsUsersResponse(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, users=None, components=None):  # noqa: E501
        """ComponentsUsersResponse - a model defined in OpenAPI

        :param users: The users of this ComponentsUsersResponse.  # noqa: E501
        :type users: List[ComponentsUser]
        :param components: The components of this ComponentsUsersResponse.  # noqa: E501
        :type components: List[OwnersAndSubscribersOfComponent]
        """
        self.openapi_types = {
            'users': List[ComponentsUser],
            'components': List[OwnersAndSubscribersOfComponent]
        }

        self.attribute_map = {
            'users': 'users',
            'components': 'components'
        }

        self._users = users
        self._components = components

    @classmethod
    def from_dict(cls, dikt) -> 'ComponentsUsersResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ComponentsUsersResponse of this ComponentsUsersResponse.  # noqa: E501
        :rtype: ComponentsUsersResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def users(self) -> List[ComponentsUser]:
        """Gets the users of this ComponentsUsersResponse.


        :return: The users of this ComponentsUsersResponse.
        :rtype: List[ComponentsUser]
        """
        return self._users

    @users.setter
    def users(self, users: List[ComponentsUser]):
        """Sets the users of this ComponentsUsersResponse.


        :param users: The users of this ComponentsUsersResponse.
        :type users: List[ComponentsUser]
        """

        self._users = users

    @property
    def components(self) -> List[OwnersAndSubscribersOfComponent]:
        """Gets the components of this ComponentsUsersResponse.


        :return: The components of this ComponentsUsersResponse.
        :rtype: List[OwnersAndSubscribersOfComponent]
        """
        return self._components

    @components.setter
    def components(self, components: List[OwnersAndSubscribersOfComponent]):
        """Sets the components of this ComponentsUsersResponse.


        :param components: The components of this ComponentsUsersResponse.
        :type components: List[OwnersAndSubscribersOfComponent]
        """

        self._components = components
