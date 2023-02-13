# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from chromestatus_openapi.models.component_subscribers import ComponentSubscribers  # noqa: E501
from chromestatus_openapi.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_list_component_subscribers(self):
        """Test case for list_component_subscribers

        List all components and possible subscribers
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/componentsubscribers',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
