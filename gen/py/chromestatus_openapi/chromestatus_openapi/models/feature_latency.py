from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi import util

from chromestatus_openapi.models.feature_link import FeatureLink  # noqa: E501

class FeatureLatency(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, feature=None, entry_created_date=None, shipped_milestone=None, shipped_date=None, owner_email=None):  # noqa: E501
        """FeatureLatency - a model defined in OpenAPI

        :param feature: The feature of this FeatureLatency.  # noqa: E501
        :type feature: FeatureLink
        :param entry_created_date: The entry_created_date of this FeatureLatency.  # noqa: E501
        :type entry_created_date: date
        :param shipped_milestone: The shipped_milestone of this FeatureLatency.  # noqa: E501
        :type shipped_milestone: int
        :param shipped_date: The shipped_date of this FeatureLatency.  # noqa: E501
        :type shipped_date: date
        :param owner_email: The owner_email of this FeatureLatency.  # noqa: E501
        :type owner_email: str
        """
        self.openapi_types = {
            'feature': FeatureLink,
            'entry_created_date': date,
            'shipped_milestone': int,
            'shipped_date': date,
            'owner_email': str
        }

        self.attribute_map = {
            'feature': 'feature',
            'entry_created_date': 'entry_created_date',
            'shipped_milestone': 'shipped_milestone',
            'shipped_date': 'shipped_date',
            'owner_email': 'owner_email'
        }

        self._feature = feature
        self._entry_created_date = entry_created_date
        self._shipped_milestone = shipped_milestone
        self._shipped_date = shipped_date
        self._owner_email = owner_email

    @classmethod
    def from_dict(cls, dikt) -> 'FeatureLatency':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FeatureLatency of this FeatureLatency.  # noqa: E501
        :rtype: FeatureLatency
        """
        return util.deserialize_model(dikt, cls)

    @property
    def feature(self) -> FeatureLink:
        """Gets the feature of this FeatureLatency.


        :return: The feature of this FeatureLatency.
        :rtype: FeatureLink
        """
        return self._feature

    @feature.setter
    def feature(self, feature: FeatureLink):
        """Sets the feature of this FeatureLatency.


        :param feature: The feature of this FeatureLatency.
        :type feature: FeatureLink
        """

        self._feature = feature

    @property
    def entry_created_date(self) -> date:
        """Gets the entry_created_date of this FeatureLatency.


        :return: The entry_created_date of this FeatureLatency.
        :rtype: date
        """
        return self._entry_created_date

    @entry_created_date.setter
    def entry_created_date(self, entry_created_date: date):
        """Sets the entry_created_date of this FeatureLatency.


        :param entry_created_date: The entry_created_date of this FeatureLatency.
        :type entry_created_date: date
        """
        if entry_created_date is None:
            raise ValueError("Invalid value for `entry_created_date`, must not be `None`")  # noqa: E501

        self._entry_created_date = entry_created_date

    @property
    def shipped_milestone(self) -> int:
        """Gets the shipped_milestone of this FeatureLatency.


        :return: The shipped_milestone of this FeatureLatency.
        :rtype: int
        """
        return self._shipped_milestone

    @shipped_milestone.setter
    def shipped_milestone(self, shipped_milestone: int):
        """Sets the shipped_milestone of this FeatureLatency.


        :param shipped_milestone: The shipped_milestone of this FeatureLatency.
        :type shipped_milestone: int
        """
        if shipped_milestone is None:
            raise ValueError("Invalid value for `shipped_milestone`, must not be `None`")  # noqa: E501

        self._shipped_milestone = shipped_milestone

    @property
    def shipped_date(self) -> date:
        """Gets the shipped_date of this FeatureLatency.


        :return: The shipped_date of this FeatureLatency.
        :rtype: date
        """
        return self._shipped_date

    @shipped_date.setter
    def shipped_date(self, shipped_date: date):
        """Sets the shipped_date of this FeatureLatency.


        :param shipped_date: The shipped_date of this FeatureLatency.
        :type shipped_date: date
        """
        if shipped_date is None:
            raise ValueError("Invalid value for `shipped_date`, must not be `None`")  # noqa: E501

        self._shipped_date = shipped_date

    @property
    def owner_email(self) -> str:
        """Gets the owner_email of this FeatureLatency.


        :return: The owner_email of this FeatureLatency.
        :rtype: str
        """
        return self._owner_email

    @owner_email.setter
    def owner_email(self, owner_email: str):
        """Sets the owner_email of this FeatureLatency.


        :param owner_email: The owner_email of this FeatureLatency.
        :type owner_email: str
        """
        if owner_email is None:
            raise ValueError("Invalid value for `owner_email`, must not be `None`")  # noqa: E501

        self._owner_email = owner_email
