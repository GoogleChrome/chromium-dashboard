# coding: utf-8

"""
    webstatus.dev API

    A tool to monitor and track the status of all Web Platform features across dimensions that are related to availability and implementation quality across browsers, and adoption by web developers. 

    The version of the OpenAPI document: 0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import json
from enum import Enum
from typing_extensions import Self


class WPTMetricView(str, Enum):
    """
    The desired view of the WPT Data
    """

    """
    allowed enum values
    """
    TEST_COUNTS = 'test_counts'
    SUBTEST_COUNTS = 'subtest_counts'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of WPTMetricView from a JSON string"""
        return cls(json.loads(json_str))


