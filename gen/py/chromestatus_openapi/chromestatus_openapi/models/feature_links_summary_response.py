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

from pydantic import BaseModel, ConfigDict, StrictInt
from typing import Any, ClassVar, Dict, List, Optional
from chromestatus_openapi.models.counter_entry import CounterEntry
from typing import Optional, Set
from typing_extensions import Self

class FeatureLinksSummaryResponse(BaseModel):
    """
    FeatureLinksSummaryResponse
    """ # noqa: E501
    total_count: Optional[StrictInt] = None
    covered_count: Optional[StrictInt] = None
    uncovered_count: Optional[StrictInt] = None
    error_count: Optional[StrictInt] = None
    http_error_count: Optional[StrictInt] = None
    link_types: Optional[List[CounterEntry]] = None
    uncovered_link_domains: Optional[List[CounterEntry]] = None
    error_link_domains: Optional[List[CounterEntry]] = None
    __properties: ClassVar[List[str]] = ["total_count", "covered_count", "uncovered_count", "error_count", "http_error_count", "link_types", "uncovered_link_domains", "error_link_domains"]

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
        """Create an instance of FeatureLinksSummaryResponse from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in link_types (list)
        _items = []
        if self.link_types:
            for _item in self.link_types:
                if _item:
                    _items.append(_item.to_dict())
            _dict['link_types'] = _items
        # override the default output from pydantic by calling `to_dict()` of each item in uncovered_link_domains (list)
        _items = []
        if self.uncovered_link_domains:
            for _item in self.uncovered_link_domains:
                if _item:
                    _items.append(_item.to_dict())
            _dict['uncovered_link_domains'] = _items
        # override the default output from pydantic by calling `to_dict()` of each item in error_link_domains (list)
        _items = []
        if self.error_link_domains:
            for _item in self.error_link_domains:
                if _item:
                    _items.append(_item.to_dict())
            _dict['error_link_domains'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FeatureLinksSummaryResponse from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "total_count": obj.get("total_count"),
            "covered_count": obj.get("covered_count"),
            "uncovered_count": obj.get("uncovered_count"),
            "error_count": obj.get("error_count"),
            "http_error_count": obj.get("http_error_count"),
            "link_types": [CounterEntry.from_dict(_item) for _item in obj["link_types"]] if obj.get("link_types") is not None else None,
            "uncovered_link_domains": [CounterEntry.from_dict(_item) for _item in obj["uncovered_link_domains"]] if obj.get("uncovered_link_domains") is not None else None,
            "error_link_domains": [CounterEntry.from_dict(_item) for _item in obj["error_link_domains"]] if obj.get("error_link_domains") is not None else None
        })
        return _obj


