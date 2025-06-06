from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi import util


class ReviewActivity(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, feature_id=None, event_type=None, event_date=None, team_name=None, review_status=None, review_assignee=None, author=None, content=None):  # noqa: E501
        """ReviewActivity - a model defined in OpenAPI

        :param feature_id: The feature_id of this ReviewActivity.  # noqa: E501
        :type feature_id: int
        :param event_type: The event_type of this ReviewActivity.  # noqa: E501
        :type event_type: str
        :param event_date: The event_date of this ReviewActivity.  # noqa: E501
        :type event_date: str
        :param team_name: The team_name of this ReviewActivity.  # noqa: E501
        :type team_name: str
        :param review_status: The review_status of this ReviewActivity.  # noqa: E501
        :type review_status: str
        :param review_assignee: The review_assignee of this ReviewActivity.  # noqa: E501
        :type review_assignee: str
        :param author: The author of this ReviewActivity.  # noqa: E501
        :type author: str
        :param content: The content of this ReviewActivity.  # noqa: E501
        :type content: str
        """
        self.openapi_types = {
            'feature_id': int,
            'event_type': str,
            'event_date': str,
            'team_name': str,
            'review_status': str,
            'review_assignee': str,
            'author': str,
            'content': str
        }

        self.attribute_map = {
            'feature_id': 'feature_id',
            'event_type': 'event_type',
            'event_date': 'event_date',
            'team_name': 'team_name',
            'review_status': 'review_status',
            'review_assignee': 'review_assignee',
            'author': 'author',
            'content': 'content'
        }

        self._feature_id = feature_id
        self._event_type = event_type
        self._event_date = event_date
        self._team_name = team_name
        self._review_status = review_status
        self._review_assignee = review_assignee
        self._author = author
        self._content = content

    @classmethod
    def from_dict(cls, dikt) -> 'ReviewActivity':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ReviewActivity of this ReviewActivity.  # noqa: E501
        :rtype: ReviewActivity
        """
        return util.deserialize_model(dikt, cls)

    @property
    def feature_id(self) -> int:
        """Gets the feature_id of this ReviewActivity.


        :return: The feature_id of this ReviewActivity.
        :rtype: int
        """
        return self._feature_id

    @feature_id.setter
    def feature_id(self, feature_id: int):
        """Sets the feature_id of this ReviewActivity.


        :param feature_id: The feature_id of this ReviewActivity.
        :type feature_id: int
        """
        if feature_id is None:
            raise ValueError("Invalid value for `feature_id`, must not be `None`")  # noqa: E501

        self._feature_id = feature_id

    @property
    def event_type(self) -> str:
        """Gets the event_type of this ReviewActivity.


        :return: The event_type of this ReviewActivity.
        :rtype: str
        """
        return self._event_type

    @event_type.setter
    def event_type(self, event_type: str):
        """Sets the event_type of this ReviewActivity.


        :param event_type: The event_type of this ReviewActivity.
        :type event_type: str
        """
        if event_type is None:
            raise ValueError("Invalid value for `event_type`, must not be `None`")  # noqa: E501

        self._event_type = event_type

    @property
    def event_date(self) -> str:
        """Gets the event_date of this ReviewActivity.


        :return: The event_date of this ReviewActivity.
        :rtype: str
        """
        return self._event_date

    @event_date.setter
    def event_date(self, event_date: str):
        """Sets the event_date of this ReviewActivity.


        :param event_date: The event_date of this ReviewActivity.
        :type event_date: str
        """
        if event_date is None:
            raise ValueError("Invalid value for `event_date`, must not be `None`")  # noqa: E501

        self._event_date = event_date

    @property
    def team_name(self) -> str:
        """Gets the team_name of this ReviewActivity.


        :return: The team_name of this ReviewActivity.
        :rtype: str
        """
        return self._team_name

    @team_name.setter
    def team_name(self, team_name: str):
        """Sets the team_name of this ReviewActivity.


        :param team_name: The team_name of this ReviewActivity.
        :type team_name: str
        """
        if team_name is None:
            raise ValueError("Invalid value for `team_name`, must not be `None`")  # noqa: E501

        self._team_name = team_name

    @property
    def review_status(self) -> str:
        """Gets the review_status of this ReviewActivity.


        :return: The review_status of this ReviewActivity.
        :rtype: str
        """
        return self._review_status

    @review_status.setter
    def review_status(self, review_status: str):
        """Sets the review_status of this ReviewActivity.


        :param review_status: The review_status of this ReviewActivity.
        :type review_status: str
        """

        self._review_status = review_status

    @property
    def review_assignee(self) -> str:
        """Gets the review_assignee of this ReviewActivity.


        :return: The review_assignee of this ReviewActivity.
        :rtype: str
        """
        return self._review_assignee

    @review_assignee.setter
    def review_assignee(self, review_assignee: str):
        """Sets the review_assignee of this ReviewActivity.


        :param review_assignee: The review_assignee of this ReviewActivity.
        :type review_assignee: str
        """

        self._review_assignee = review_assignee

    @property
    def author(self) -> str:
        """Gets the author of this ReviewActivity.


        :return: The author of this ReviewActivity.
        :rtype: str
        """
        return self._author

    @author.setter
    def author(self, author: str):
        """Sets the author of this ReviewActivity.


        :param author: The author of this ReviewActivity.
        :type author: str
        """
        if author is None:
            raise ValueError("Invalid value for `author`, must not be `None`")  # noqa: E501

        self._author = author

    @property
    def content(self) -> str:
        """Gets the content of this ReviewActivity.


        :return: The content of this ReviewActivity.
        :rtype: str
        """
        return self._content

    @content.setter
    def content(self, content: str):
        """Sets the content of this ReviewActivity.


        :param content: The content of this ReviewActivity.
        :type content: str
        """

        self._content = content
