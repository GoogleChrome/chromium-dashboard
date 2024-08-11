import unittest

from flask import json

from chromestatus_openapi.models.account_response import AccountResponse  # noqa: E501
from chromestatus_openapi.models.component_users_request import ComponentUsersRequest  # noqa: E501
from chromestatus_openapi.models.components_users_response import ComponentsUsersResponse  # noqa: E501
from chromestatus_openapi.models.create_account_request import CreateAccountRequest  # noqa: E501
from chromestatus_openapi.models.create_origin_trial_request import CreateOriginTrialRequest  # noqa: E501
from chromestatus_openapi.models.delete_account200_response import DeleteAccount200Response  # noqa: E501
from chromestatus_openapi.models.dismiss_cue_request import DismissCueRequest  # noqa: E501
from chromestatus_openapi.models.error_message import ErrorMessage  # noqa: E501
from chromestatus_openapi.models.external_reviews_response import ExternalReviewsResponse  # noqa: E501
from chromestatus_openapi.models.feature_latency import FeatureLatency  # noqa: E501
from chromestatus_openapi.models.get_dismissed_cues400_response import GetDismissedCues400Response  # noqa: E501
from chromestatus_openapi.models.get_intent_response import GetIntentResponse  # noqa: E501
from chromestatus_openapi.models.get_origin_trials_response import GetOriginTrialsResponse  # noqa: E501
from chromestatus_openapi.models.message_response import MessageResponse  # noqa: E501
from chromestatus_openapi.models.post_intent_request import PostIntentRequest  # noqa: E501
from chromestatus_openapi.models.review_latency import ReviewLatency  # noqa: E501
from chromestatus_openapi.models.spec_mentor import SpecMentor  # noqa: E501
from chromestatus_openapi.models.success_message import SuccessMessage  # noqa: E501
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

    def test_create_origin_trial(self):
        """Test case for create_origin_trial

        Create a new origin trial
        """
        create_origin_trial_request = {"finch_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_display_name":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"rollout_platforms":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_feedback_submission_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"desktop_last":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"android_first":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"android_last":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"announcement_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_description":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"rollout_details":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_approval_buganizer_component":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_approval_criteria_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_approval_group_email":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"experiment_extension_reason":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"rollout_milestone":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_owner_email":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_request_note":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ios_last":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"browser":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"webview_first":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_documentation_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_emails":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_require_approvals":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_has_third_party_support":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"experiment_goals":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_stage_id":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_approval_buganizer_custom_field_id":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"intent_thread_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_is_critical_trial":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"display_name":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_is_deprecation_trial":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"rollout_impact":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"origin_trial_feedback_url":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"desktop_first":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"experiment_risks":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ios_first":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_action_requested":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"origin_trial_id":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"webview_last":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"enterprise_policies":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_chromium_trial_name":{"form_field_name":"form_field_name","value":"FieldInfo_value"},"ot_webfeature_use_counter":{"form_field_name":"form_field_name","value":"FieldInfo_value"}}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/origintrials/{feature_id}/{stage_id}/create'.format(feature_id=56, stage_id=56),
            method='POST',
            headers=headers,
            data=json.dumps(create_origin_trial_request),
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

    def test_dismiss_cue(self):
        """Test case for dismiss_cue

        Dismiss a cue card for the signed-in user
        """
        dismiss_cue_request = {"cue":"progress-checkmarks"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v0/currentuser/cues',
            method='POST',
            headers=headers,
            data=json.dumps(dismiss_cue_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_extend_origin_trial(self):
        """Test case for extend_origin_trial

        Extend an existing origin trial
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/origintrials/{feature_id}/{extension_stage_id}/extend'.format(feature_id=56, extension_stage_id=56),
            method='PATCH',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_dismissed_cues(self):
        """Test case for get_dismissed_cues

        Get dismissed cues for the current user
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/currentuser/cues',
            method='GET',
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

    def test_get_origin_trials(self):
        """Test case for get_origin_trials

        Get origin trials
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v0/origintrials',
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
