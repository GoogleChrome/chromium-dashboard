import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from chromestatus_openapi.models.account_response import AccountResponse  # noqa: E501
from chromestatus_openapi.models.activity import Activity  # noqa: E501
from chromestatus_openapi.models.comments_request import CommentsRequest  # noqa: E501
from chromestatus_openapi.models.component_users_request import ComponentUsersRequest  # noqa: E501
from chromestatus_openapi.models.components_users_response import ComponentsUsersResponse  # noqa: E501
from chromestatus_openapi.models.create_account_request import CreateAccountRequest  # noqa: E501
from chromestatus_openapi.models.create_origin_trial_request import CreateOriginTrialRequest  # noqa: E501
from chromestatus_openapi.models.delete_account200_response import DeleteAccount200Response  # noqa: E501
from chromestatus_openapi.models.dismiss_cue_request import DismissCueRequest  # noqa: E501
from chromestatus_openapi.models.error_message import ErrorMessage  # noqa: E501
from chromestatus_openapi.models.external_reviews_response import ExternalReviewsResponse  # noqa: E501
from chromestatus_openapi.models.feature_latency import FeatureLatency  # noqa: E501
from chromestatus_openapi.models.feature_links_response import FeatureLinksResponse  # noqa: E501
from chromestatus_openapi.models.feature_links_sample import FeatureLinksSample  # noqa: E501
from chromestatus_openapi.models.feature_links_summary_response import FeatureLinksSummaryResponse  # noqa: E501
from chromestatus_openapi.models.get_comments_response import GetCommentsResponse  # noqa: E501
from chromestatus_openapi.models.get_dismissed_cues400_response import GetDismissedCues400Response  # noqa: E501
from chromestatus_openapi.models.get_gate_response import GetGateResponse  # noqa: E501
from chromestatus_openapi.models.get_intent_response import GetIntentResponse  # noqa: E501
from chromestatus_openapi.models.get_origin_trials_response import GetOriginTrialsResponse  # noqa: E501
from chromestatus_openapi.models.get_settings_response import GetSettingsResponse  # noqa: E501
from chromestatus_openapi.models.get_stars_response import GetStarsResponse  # noqa: E501
from chromestatus_openapi.models.get_votes_response import GetVotesResponse  # noqa: E501
from chromestatus_openapi.models.message_response import MessageResponse  # noqa: E501
from chromestatus_openapi.models.patch_comment_request import PatchCommentRequest  # noqa: E501
from chromestatus_openapi.models.permissions_response import PermissionsResponse  # noqa: E501
from chromestatus_openapi.models.post_gate_request import PostGateRequest  # noqa: E501
from chromestatus_openapi.models.post_intent_request import PostIntentRequest  # noqa: E501
from chromestatus_openapi.models.post_settings_request import PostSettingsRequest  # noqa: E501
from chromestatus_openapi.models.post_vote_request import PostVoteRequest  # noqa: E501
from chromestatus_openapi.models.process import Process  # noqa: E501
from chromestatus_openapi.models.reject_unneeded_get_request import RejectUnneededGetRequest  # noqa: E501
from chromestatus_openapi.models.review_latency import ReviewLatency  # noqa: E501
from chromestatus_openapi.models.set_star_request import SetStarRequest  # noqa: E501
from chromestatus_openapi.models.sign_in_request import SignInRequest  # noqa: E501
from chromestatus_openapi.models.spec_mentor import SpecMentor  # noqa: E501
from chromestatus_openapi.models.success_message import SuccessMessage  # noqa: E501
from chromestatus_openapi import util


def add_feature_comment(feature_id, comments_request=None):  # noqa: E501
    """Add a comment to a feature

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param comments_request: Add a review commend and possible set a approval value
    :type comments_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        comments_request = CommentsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def add_gate_comment(feature_id, gate_id, comments_request=None):  # noqa: E501
    """Add a comment to a specific gate

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param gate_id: 
    :type gate_id: int
    :param comments_request: 
    :type comments_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        comments_request = CommentsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def add_user_to_component(component_id, user_id, component_users_request=None):  # noqa: E501
    """Add a user to a component

     # noqa: E501

    :param component_id: Component ID
    :type component_id: int
    :param user_id: User ID
    :type user_id: int
    :param component_users_request: 
    :type component_users_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        component_users_request = ComponentUsersRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def add_xfn_gates_to_stage(feature_id, stage_id):  # noqa: E501
    """Add a full set of cross-functional gates to a stage.

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param stage_id: 
    :type stage_id: int

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    return 'do some magic!'


def authenticate_user(sign_in_request):  # noqa: E501
    """Authenticate user with Google Sign-In

     # noqa: E501

    :param sign_in_request: 
    :type sign_in_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        sign_in_request = SignInRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_account(create_account_request=None):  # noqa: E501
    """Create a new account

     # noqa: E501

    :param create_account_request: 
    :type create_account_request: dict | bytes

    :rtype: Union[AccountResponse, Tuple[AccountResponse, int], Tuple[AccountResponse, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        create_account_request = CreateAccountRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_origin_trial(feature_id, stage_id, create_origin_trial_request=None):  # noqa: E501
    """Create a new origin trial

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param stage_id: 
    :type stage_id: int
    :param create_origin_trial_request: 
    :type create_origin_trial_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        create_origin_trial_request = CreateOriginTrialRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_account(account_id):  # noqa: E501
    """Delete an account

     # noqa: E501

    :param account_id: ID of the account to delete
    :type account_id: int

    :rtype: Union[DeleteAccount200Response, Tuple[DeleteAccount200Response, int], Tuple[DeleteAccount200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def dismiss_cue(dismiss_cue_request):  # noqa: E501
    """Dismiss a cue card for the signed-in user

     # noqa: E501

    :param dismiss_cue_request: 
    :type dismiss_cue_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        dismiss_cue_request = DismissCueRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def extend_origin_trial(feature_id, extension_stage_id):  # noqa: E501
    """Extend an existing origin trial

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param extension_stage_id: 
    :type extension_stage_id: int

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_dismissed_cues():  # noqa: E501
    """Get dismissed cues for the current user

     # noqa: E501


    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feature_comments(feature_id):  # noqa: E501
    """Get all comments for a given feature

     # noqa: E501

    :param feature_id: 
    :type feature_id: int

    :rtype: Union[GetCommentsResponse, Tuple[GetCommentsResponse, int], Tuple[GetCommentsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feature_links(feature_id=None, update_stale_links=None):  # noqa: E501
    """Get feature links by feature_id

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param update_stale_links: 
    :type update_stale_links: bool

    :rtype: Union[FeatureLinksResponse, Tuple[FeatureLinksResponse, int], Tuple[FeatureLinksResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feature_links_samples(domain=None, type=None, is_error=None):  # noqa: E501
    """Get feature links samples

     # noqa: E501

    :param domain: 
    :type domain: str
    :param type: 
    :type type: str
    :param is_error: 
    :type is_error: bool

    :rtype: Union[FeatureLinksSample, Tuple[FeatureLinksSample, int], Tuple[FeatureLinksSample, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feature_links_summary():  # noqa: E501
    """Get feature links summary

     # noqa: E501


    :rtype: Union[FeatureLinksSummaryResponse, Tuple[FeatureLinksSummaryResponse, int], Tuple[FeatureLinksSummaryResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_gate_comments(feature_id, gate_id):  # noqa: E501
    """Get all comments for a given gate

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param gate_id: 
    :type gate_id: int

    :rtype: Union[List[Activity], Tuple[List[Activity], int], Tuple[List[Activity], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_gates_for_feature(feature_id):  # noqa: E501
    """Get all gates for a feature

     # noqa: E501

    :param feature_id: The ID of the feature to retrieve votes for.
    :type feature_id: int

    :rtype: Union[GetGateResponse, Tuple[GetGateResponse, int], Tuple[GetGateResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_intent_body(feature_id, stage_id, gate_id):  # noqa: E501
    """Get the HTML body of an intent draft

     # noqa: E501

    :param feature_id: Feature ID
    :type feature_id: int
    :param stage_id: Stage ID
    :type stage_id: int
    :param gate_id: Gate ID
    :type gate_id: int

    :rtype: Union[GetIntentResponse, Tuple[GetIntentResponse, int], Tuple[GetIntentResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_origin_trials():  # noqa: E501
    """Get origin trials

     # noqa: E501


    :rtype: Union[GetOriginTrialsResponse, Tuple[GetOriginTrialsResponse, int], Tuple[GetOriginTrialsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pending_gates():  # noqa: E501
    """Get all pending gates

     # noqa: E501


    :rtype: Union[GetGateResponse, Tuple[GetGateResponse, int], Tuple[GetGateResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_process(feature_id):  # noqa: E501
    """Get the process for a feature

     # noqa: E501

    :param feature_id: Feature ID
    :type feature_id: int

    :rtype: Union[Process, Tuple[Process, int], Tuple[Process, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_progress(feature_id):  # noqa: E501
    """Get the progress for a feature

     # noqa: E501

    :param feature_id: Feature ID
    :type feature_id: int

    :rtype: Union[Dict[str, object], Tuple[Dict[str, object], int], Tuple[Dict[str, object], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_stars():  # noqa: E501
    """Get a list of all starred feature IDs for the signed-in user

     # noqa: E501


    :rtype: Union[List[GetStarsResponse], Tuple[List[GetStarsResponse], int], Tuple[List[GetStarsResponse], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user_permissions(return_paired_user=None):  # noqa: E501
    """Get the permissions and email of the user

     # noqa: E501

    :param return_paired_user: If true, return the permissions of the paired user.
    :type return_paired_user: bool

    :rtype: Union[PermissionsResponse, Tuple[PermissionsResponse, int], Tuple[PermissionsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user_settings():  # noqa: E501
    """Get user settings

     # noqa: E501


    :rtype: Union[GetSettingsResponse, Tuple[GetSettingsResponse, int], Tuple[GetSettingsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_votes_for_feature(feature_id):  # noqa: E501
    """Get votes for a feature

     # noqa: E501

    :param feature_id: Feature ID
    :type feature_id: int

    :rtype: Union[GetVotesResponse, Tuple[GetVotesResponse, int], Tuple[GetVotesResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_votes_for_feature_and_gate(feature_id, gate_id):  # noqa: E501
    """Get votes for a feature and gate

     # noqa: E501

    :param feature_id: The ID of the feature to retrieve votes for.
    :type feature_id: int
    :param gate_id: The ID of the gate associated with the votes.
    :type gate_id: int

    :rtype: Union[GetVotesResponse, Tuple[GetVotesResponse, int], Tuple[GetVotesResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_component_users():  # noqa: E501
    """List all components and possible users

     # noqa: E501


    :rtype: Union[ComponentsUsersResponse, Tuple[ComponentsUsersResponse, int], Tuple[ComponentsUsersResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_external_reviews(review_group):  # noqa: E501
    """List features whose external reviews are incomplete

     # noqa: E501

    :param review_group: Which review group to focus on:  * &#x60;tag&#x60; - The W3C TAG  * &#x60;gecko&#x60; - The rendering engine that powers Mozilla Firefox  * &#x60;webkit&#x60; - The rendering engine that powers Apple Safari 
    :type review_group: str

    :rtype: Union[ExternalReviewsResponse, Tuple[ExternalReviewsResponse, int], Tuple[ExternalReviewsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_feature_latency(start_at, end_at):  # noqa: E501
    """List how long each feature took to launch

     # noqa: E501

    :param start_at: Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    :type start_at: str
    :param end_at: End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    :type end_at: str

    :rtype: Union[List[FeatureLatency], Tuple[List[FeatureLatency], int], Tuple[List[FeatureLatency], int, Dict[str, str]]
    """
    start_at = util.deserialize_date(start_at)
    end_at = util.deserialize_date(end_at)
    return 'do some magic!'


def list_reviews_with_latency():  # noqa: E501
    """List recently reviewed features and their review latency

     # noqa: E501


    :rtype: Union[List[ReviewLatency], Tuple[List[ReviewLatency], int], Tuple[List[ReviewLatency], int, Dict[str, str]]
    """
    return 'do some magic!'


def list_spec_mentors(after=None):  # noqa: E501
    """List spec mentors and their activity

     # noqa: E501

    :param after: 
    :type after: str

    :rtype: Union[List[SpecMentor], Tuple[List[SpecMentor], int], Tuple[List[SpecMentor], int, Dict[str, str]]
    """
    after = util.deserialize_date(after)
    return 'do some magic!'


def logout_user():  # noqa: E501
    """Log out the current user

     # noqa: E501


    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    return 'do some magic!'


def post_intent_to_blink_dev(feature_id, stage_id, gate_id, post_intent_request=None):  # noqa: E501
    """Submit an intent to be posted on blink-dev

     # noqa: E501

    :param feature_id: Feature ID
    :type feature_id: int
    :param stage_id: Stage ID
    :type stage_id: int
    :param gate_id: Gate ID
    :type gate_id: int
    :param post_intent_request: Gate ID and additional users to CC email to.
    :type post_intent_request: dict | bytes

    :rtype: Union[MessageResponse, Tuple[MessageResponse, int], Tuple[MessageResponse, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        post_intent_request = PostIntentRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def refresh_token():  # noqa: E501
    """Refresh the XSRF token

     # noqa: E501


    :rtype: Union[List[ReviewLatency], Tuple[List[ReviewLatency], int], Tuple[List[ReviewLatency], int, Dict[str, str]]
    """
    return 'do some magic!'


def reject_get_requests_login():  # noqa: E501
    """reject unneeded GET request without triggering Error Reporting

     # noqa: E501


    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def reject_get_requests_logout():  # noqa: E501
    """reject unneeded GET request without triggering Error Reporting

     # noqa: E501


    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def remove_user_from_component(component_id, user_id, component_users_request=None):  # noqa: E501
    """Remove a user from a component

     # noqa: E501

    :param component_id: Component ID
    :type component_id: int
    :param user_id: User ID
    :type user_id: int
    :param component_users_request: 
    :type component_users_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        component_users_request = ComponentUsersRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def set_assignees_for_gate(feature_id, gate_id, post_gate_request):  # noqa: E501
    """Set the assignees for a gate.

     # noqa: E501

    :param feature_id: The ID of the feature to retrieve votes for.
    :type feature_id: int
    :param gate_id: The ID of the gate to retrieve votes for.
    :type gate_id: int
    :param post_gate_request: 
    :type post_gate_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        post_gate_request = PostGateRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def set_star(set_star_request):  # noqa: E501
    """Set or clear a star on the specified feature

     # noqa: E501

    :param set_star_request: 
    :type set_star_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        set_star_request = SetStarRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def set_user_settings(post_settings_request):  # noqa: E501
    """Set the user settings (currently only the notify_as_starrer)

     # noqa: E501

    :param post_settings_request: 
    :type post_settings_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        post_settings_request = PostSettingsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def set_vote_for_feature_and_gate(feature_id, gate_id, post_vote_request):  # noqa: E501
    """Set a user&#39;s vote value for the specific feature and gate.

     # noqa: E501

    :param feature_id: The ID of the feature to retrieve votes for.
    :type feature_id: int
    :param gate_id: The ID of the gate associated with the votes.
    :type gate_id: int
    :param post_vote_request: 
    :type post_vote_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        post_vote_request = PostVoteRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_feature_comment(feature_id, patch_comment_request):  # noqa: E501
    """Update a comment on a feature

     # noqa: E501

    :param feature_id: 
    :type feature_id: int
    :param patch_comment_request: 
    :type patch_comment_request: dict | bytes

    :rtype: Union[SuccessMessage, Tuple[SuccessMessage, int], Tuple[SuccessMessage, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        patch_comment_request = PatchCommentRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
