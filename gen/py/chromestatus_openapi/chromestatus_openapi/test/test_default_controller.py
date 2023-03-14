# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from chromestatus_openapi.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_componentsusers_get(self):
        """Test case for componentsusers_get

        
        """
        headers = { 
        }
        response = self.client.open(
            '/api/v0/componentsusers',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
