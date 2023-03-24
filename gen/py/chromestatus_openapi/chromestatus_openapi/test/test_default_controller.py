# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from chromestatus_openapi.models.component_users_request import ComponentUsersRequest  # noqa: E501
from chromestatus_openapi.models.components_users_response import ComponentsUsersResponse  # noqa: E501
from chromestatus_openapi.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_add_user_to_component(self):
        """Test case for add_user_to_component

        Add a user to a component
        """
        component_users_request = {"owner":True}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/components/{component_id}/users/{user_id}'.format(component_id=56, user_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(component_users_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_component_users(self):
        """Test case for list_component_users

        List all components and possible users
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/componentsusers',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_user_from_component(self):
        """Test case for remove_user_from_component

        Remove a user from a component
        """
        component_users_request = {"owner":True}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/components/{component_id}/users/{user_id}'.format(component_id=56, user_id=56),
            method='DELETE',
            headers=headers,
            data=json.dumps(component_users_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
