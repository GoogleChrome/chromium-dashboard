# coding: utf-8

"""
    webstatus.dev API

    A tool to monitor and track the status of all Web Platform features across dimensions that are related to availability and implementation quality across browsers, and adoption by web developers. 

    The version of the OpenAPI document: 0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict
from typing import Any, ClassVar, Dict, List, Optional
from webstatus_openapi.models.browser_release_feature_metric import BrowserReleaseFeatureMetric
from webstatus_openapi.models.page_metadata import PageMetadata
from typing import Optional, Set
from typing_extensions import Self

class BrowserReleaseFeatureMetricsPage(BaseModel):
    """
    BrowserReleaseFeatureMetricsPage
    """ # noqa: E501
    metadata: Optional[PageMetadata] = None
    data: List[BrowserReleaseFeatureMetric]
    __properties: ClassVar[List[str]] = ["metadata", "data"]

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
        """Create an instance of BrowserReleaseFeatureMetricsPage from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of metadata
        if self.metadata:
            _dict['metadata'] = self.metadata.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in data (list)
        _items = []
        if self.data:
            for _item in self.data:
                if _item:
                    _items.append(_item.to_dict())
            _dict['data'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of BrowserReleaseFeatureMetricsPage from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "metadata": PageMetadata.from_dict(obj["metadata"]) if obj.get("metadata") is not None else None,
            "data": [BrowserReleaseFeatureMetric.from_dict(_item) for _item in obj["data"]] if obj.get("data") is not None else None
        })
        return _obj


