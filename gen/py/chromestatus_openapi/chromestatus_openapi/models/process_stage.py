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

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from chromestatus_openapi.models.action import Action
from chromestatus_openapi.models.gate_info import GateInfo
from chromestatus_openapi.models.progress_item import ProgressItem
from typing import Optional, Set
from typing_extensions import Self

class ProcessStage(BaseModel):
    """
    ProcessStage
    """ # noqa: E501
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    progress_items: Optional[List[ProgressItem]] = None
    actions: Optional[List[Action]] = None
    approvals: Optional[List[GateInfo]] = None
    incoming_stage: Optional[StrictInt] = None
    outgoing_stage: Optional[StrictInt] = None
    stage_type: Optional[StrictInt] = None
    __properties: ClassVar[List[str]] = ["name", "description", "progress_items", "actions", "approvals", "incoming_stage", "outgoing_stage", "stage_type"]

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
        """Create an instance of ProcessStage from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in progress_items (list)
        _items = []
        if self.progress_items:
            for _item in self.progress_items:
                if _item:
                    _items.append(_item.to_dict())
            _dict['progress_items'] = _items
        # override the default output from pydantic by calling `to_dict()` of each item in actions (list)
        _items = []
        if self.actions:
            for _item in self.actions:
                if _item:
                    _items.append(_item.to_dict())
            _dict['actions'] = _items
        # override the default output from pydantic by calling `to_dict()` of each item in approvals (list)
        _items = []
        if self.approvals:
            for _item in self.approvals:
                if _item:
                    _items.append(_item.to_dict())
            _dict['approvals'] = _items
        # set to None if stage_type (nullable) is None
        # and model_fields_set contains the field
        if self.stage_type is None and "stage_type" in self.model_fields_set:
            _dict['stage_type'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ProcessStage from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "name": obj.get("name"),
            "description": obj.get("description"),
            "progress_items": [ProgressItem.from_dict(_item) for _item in obj["progress_items"]] if obj.get("progress_items") is not None else None,
            "actions": [Action.from_dict(_item) for _item in obj["actions"]] if obj.get("actions") is not None else None,
            "approvals": [GateInfo.from_dict(_item) for _item in obj["approvals"]] if obj.get("approvals") is not None else None,
            "incoming_stage": obj.get("incoming_stage"),
            "outgoing_stage": obj.get("outgoing_stage"),
            "stage_type": obj.get("stage_type")
        })
        return _obj


