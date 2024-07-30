import unittest

from flask import json

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
            'XsrfToken': 'special-key',
        }
        response = self.client.open(
            '/api/v0/components/{component_id}/users/{user_id}'.format(component_id=56, user_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(component_users_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_account(self):
        """Test case for create_account

        Create a new account
        """
        create_account_request = {"isSiteEditor":True,"isAdmin":True,"email":"email"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/accounts',
            method='POST',
            headers=headers,
            data=json.dumps(create_account_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_account(self):
        """Test case for delete_account

        Delete an account
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/accounts/{account_id}'.format(account_id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_intent_body(self):
        """Test case for get_intent_body

        Get the HTML body of an intent draft
        """
        headers = { 
            'Accept': 'application/json:',
        }
        response = self.client.open(
            '/api/v0/features/{feature_id}/{stage_id}/{gate_id}/intent'.format(feature_id=56, stage_id=56, gate_id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_component_users(self):
        """Test case for list_component_users

        List all components and possible users
        """
        headers = { 
            'Accept': 'application/json',
            'XsrfToken': 'special-key',
        }
        response = self.client.open(
            '/api/v0/componentsusers',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_external_reviews(self):
        """Test case for list_external_reviews

        List features whose external reviews are incomplete
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/external_reviews/{review_group}'.format(review_group='review_group_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_feature_latency(self):
        """Test case for list_feature_latency

        List how long each feature took to launch
        """
        query_string = [('startAt', '2013-10-20'),
                        ('endAt', '2013-10-20')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/feature-latency',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_reviews_with_latency(self):
        """Test case for list_reviews_with_latency

        List recently reviewed features and their review latency
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/review-latency',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_spec_mentors(self):
        """Test case for list_spec_mentors

        List spec mentors and their activity
        """
        query_string = [('after', '2013-10-20')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/spec_mentors',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_post_intent_to_blink_dev(self):
        """Test case for post_intent_to_blink_dev

        Submit an intent to be posted on blink-dev
        """
        post_intent_request = {"intent_cc_emails":["intent_cc_emails","intent_cc_emails"],"gate_id":0}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/features/{feature_id}/{stage_id}/{gate_id}/intent'.format(feature_id=56, stage_id=56, gate_id=56),
            method='POST',
            headers=headers,
            data=json.dumps(post_intent_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_user_from_component(self):
        """Test case for remove_user_from_component

        Remove a user from a component
        """
        component_users_request = {"owner":True}
        headers = { 
            'Content-Type': 'application/json',
            'XsrfToken': 'special-key',
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
