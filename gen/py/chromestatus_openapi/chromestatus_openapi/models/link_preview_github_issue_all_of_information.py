# coding: utf-8

"""
    chomestatus API

    The API for chromestatus.com. chromestatus.com is the official tool used for tracking feature launches in Blink (the browser engine that powers Chrome and many other web browsers). This tool guides feature owners through our launch process and serves as a primary source for developer information that then ripples throughout the web developer ecosystem. More details at: https://github.com/GoogleChrome/chromium-dashboard

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing import Optional, Set
from typing_extensions import Self

class LinkPreviewGithubIssueAllOfInformation(BaseModel):
    """
    LinkPreviewGithubIssueAllOfInformation
    """ # noqa: E501
    url: Optional[StrictStr] = None
    number: Optional[StrictInt] = None
    title: Optional[StrictStr] = None
    user_login: Optional[StrictStr] = None
    state: Optional[StrictStr] = None
    state_reason: Optional[StrictStr] = None
    assignee_login: Optional[StrictStr] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    labels: Optional[List[StrictStr]] = None
    __properties: ClassVar[List[str]] = ["url", "number", "title", "user_login", "state", "state_reason", "assignee_login", "created_at", "updated_at", "closed_at", "labels"]

    @field_validator('state')
    def state_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['open', 'closed']):
            raise ValueError("must be one of enum values ('open', 'closed')")
        return value

    @field_validator('state_reason')
    def state_reason_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['completed', 'reopened', 'not_planned']):
            raise ValueError("must be one of enum values ('completed', 'reopened', 'not_planned')")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        protected_namespaces=(),
    )


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of LinkPreviewGithubIssueAllOfInformation from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        excluded_fields: Set[str] = set([
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of LinkPreviewGithubIssueAllOfInformation from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "url": obj.get("url"),
            "number": obj.get("number"),
            "title": obj.get("title"),
            "user_login": obj.get("user_login"),
            "state": obj.get("state"),
            "state_reason": obj.get("state_reason"),
            "assignee_login": obj.get("assignee_login"),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "closed_at": obj.get("closed_at"),
            "labels": obj.get("labels")
        })
        return _obj


