# chromestatus_openapi.DefaultApi

All URIs are relative to */api/v0*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_feature_comment**](DefaultApi.md#add_feature_comment) | **POST** /features/&lt;int:feature_id&gt;/approvals/comments | Add a comment to a feature
[**add_gate_comment**](DefaultApi.md#add_gate_comment) | **POST** /features/&lt;int:feature_id&gt;/approvals/&lt;int:gate_id&gt;/comments | Add a comment to a specific gate
[**add_user_to_component**](DefaultApi.md#add_user_to_component) | **PUT** /components/{componentId}/users/{userId} | Add a user to a component
[**add_xfn_gates_to_stage**](DefaultApi.md#add_xfn_gates_to_stage) | **POST** /features/{feature_id}/stages/{stage_id}/addXfnGates | Add a full set of cross-functional gates to a stage.
[**authenticate_user**](DefaultApi.md#authenticate_user) | **POST** /login | Authenticate user with Google Sign-In
[**create_account**](DefaultApi.md#create_account) | **POST** /accounts | Create a new account
[**create_origin_trial**](DefaultApi.md#create_origin_trial) | **POST** /origintrials/{feature_id}/{stage_id}/create | Create a new origin trial
[**delete_account**](DefaultApi.md#delete_account) | **DELETE** /accounts/{account_id} | Delete an account
[**dismiss_cue**](DefaultApi.md#dismiss_cue) | **POST** /currentuser/cues | Dismiss a cue card for the signed-in user
[**extend_origin_trial**](DefaultApi.md#extend_origin_trial) | **PATCH** /origintrials/{feature_id}/{extension_stage_id}/extend | Extend an existing origin trial
[**get_dismissed_cues**](DefaultApi.md#get_dismissed_cues) | **GET** /currentuser/cues | Get dismissed cues for the current user
[**get_feature_comments**](DefaultApi.md#get_feature_comments) | **GET** /features/&lt;int:feature_id&gt;/approvals/comments | Get all comments for a given feature
[**get_feature_links**](DefaultApi.md#get_feature_links) | **GET** /feature_links | Get feature links by feature_id
[**get_feature_links_samples**](DefaultApi.md#get_feature_links_samples) | **GET** /feature_links_samples | Get feature links samples
[**get_feature_links_summary**](DefaultApi.md#get_feature_links_summary) | **GET** /feature_links_summary | Get feature links summary
[**get_gate_comments**](DefaultApi.md#get_gate_comments) | **GET** /features/&lt;int:feature_id&gt;/approvals/&lt;int:gate_id&gt;/comments | Get all comments for a given gate
[**get_gates_for_feature**](DefaultApi.md#get_gates_for_feature) | **GET** /features/{feature_id}/gates | Get all gates for a feature
[**get_intent_body**](DefaultApi.md#get_intent_body) | **GET** /features/{feature_id}/{stage_id}/{gate_id}/intent | Get the HTML body of an intent draft
[**get_origin_trials**](DefaultApi.md#get_origin_trials) | **GET** /origintrials | Get origin trials
[**get_pending_gates**](DefaultApi.md#get_pending_gates) | **GET** /gates/pending | Get all pending gates
[**get_process**](DefaultApi.md#get_process) | **GET** /features/{feature_id}/process | Get the process for a feature
[**get_progress**](DefaultApi.md#get_progress) | **GET** /features/{feature_id}/progress | Get the progress for a feature
[**get_stars**](DefaultApi.md#get_stars) | **GET** /currentuser/stars | Get a list of all starred feature IDs for the signed-in user
[**get_user_permissions**](DefaultApi.md#get_user_permissions) | **GET** /currentuser/permissions | Get the permissions and email of the user
[**get_user_settings**](DefaultApi.md#get_user_settings) | **GET** /currentuser/settings | Get user settings
[**get_votes_for_feature**](DefaultApi.md#get_votes_for_feature) | **GET** /features/{feature_id}/votes | Get votes for a feature
[**get_votes_for_feature_and_gate**](DefaultApi.md#get_votes_for_feature_and_gate) | **GET** /features/{feature_id}/votes/{gate_id} | Get votes for a feature and gate
[**list_component_users**](DefaultApi.md#list_component_users) | **GET** /componentsusers | List all components and possible users
[**list_external_reviews**](DefaultApi.md#list_external_reviews) | **GET** /external_reviews/{review_group} | List features whose external reviews are incomplete
[**list_feature_latency**](DefaultApi.md#list_feature_latency) | **GET** /feature-latency | List how long each feature took to launch
[**list_reviews_with_latency**](DefaultApi.md#list_reviews_with_latency) | **GET** /review-latency | List recently reviewed features and their review latency
[**list_spec_mentors**](DefaultApi.md#list_spec_mentors) | **GET** /spec_mentors | List spec mentors and their activity
[**logout_user**](DefaultApi.md#logout_user) | **POST** /logout | Log out the current user
[**post_intent_to_blink_dev**](DefaultApi.md#post_intent_to_blink_dev) | **POST** /features/{feature_id}/{stage_id}/{gate_id}/intent | Submit an intent to be posted on blink-dev
[**refresh_token**](DefaultApi.md#refresh_token) | **POST** /currentuser/token | Refresh the XSRF token
[**reject_get_requests_login**](DefaultApi.md#reject_get_requests_login) | **GET** /login | reject unneeded GET request without triggering Error Reporting
[**reject_get_requests_logout**](DefaultApi.md#reject_get_requests_logout) | **GET** /logout | reject unneeded GET request without triggering Error Reporting
[**remove_user_from_component**](DefaultApi.md#remove_user_from_component) | **DELETE** /components/{componentId}/users/{userId} | Remove a user from a component
[**set_assignees_for_gate**](DefaultApi.md#set_assignees_for_gate) | **POST** /features/{feature_id}/gates/{gate_id} | Set the assignees for a gate.
[**set_star**](DefaultApi.md#set_star) | **POST** /currentuser/stars | Set or clear a star on the specified feature
[**set_user_settings**](DefaultApi.md#set_user_settings) | **POST** /currentuser/settings | Set the user settings (currently only the notify_as_starrer)
[**set_vote_for_feature_and_gate**](DefaultApi.md#set_vote_for_feature_and_gate) | **POST** /features/{feature_id}/votes/{gate_id} | Set a user&#39;s vote value for the specific feature and gate.
[**update_feature_comment**](DefaultApi.md#update_feature_comment) | **PATCH** /features/&lt;int:feature_id&gt;/approvals/comments | Update a comment on a feature


# **add_feature_comment**
> SuccessMessage add_feature_comment(feature_id, comments_request=comments_request)

Add a comment to a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.comments_request import CommentsRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    comments_request = chromestatus_openapi.CommentsRequest() # CommentsRequest | Add a review commend and possible set a approval value (optional)

    try:
        # Add a comment to a feature
        api_response = api_instance.add_feature_comment(feature_id, comments_request=comments_request)
        print("The response of DefaultApi->add_feature_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->add_feature_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **comments_request** | [**CommentsRequest**](CommentsRequest.md)| Add a review commend and possible set a approval value | [optional] 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Comment added successfully |  -  |
**403** | User is not allowed to comment on this feature |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **add_gate_comment**
> SuccessMessage add_gate_comment(feature_id, gate_id, comments_request=comments_request)

Add a comment to a specific gate

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.comments_request import CommentsRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    gate_id = 56 # int | 
    comments_request = chromestatus_openapi.CommentsRequest() # CommentsRequest |  (optional)

    try:
        # Add a comment to a specific gate
        api_response = api_instance.add_gate_comment(feature_id, gate_id, comments_request=comments_request)
        print("The response of DefaultApi->add_gate_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->add_gate_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **gate_id** | **int**|  | 
 **comments_request** | [**CommentsRequest**](CommentsRequest.md)|  | [optional] 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Comment added successfully |  -  |
**403** | User is not allowed to comment on this gate |  -  |
**404** | Gate not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **add_user_to_component**
> add_user_to_component(component_id, user_id, component_users_request=component_users_request)

Add a user to a component

### Example

* Api Key Authentication (XsrfToken):

```python
import chromestatus_openapi
from chromestatus_openapi.models.component_users_request import ComponentUsersRequest
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: XsrfToken
configuration.api_key['XsrfToken'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['XsrfToken'] = 'Bearer'

# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    component_id = 56 # int | Component ID
    user_id = 56 # int | User ID
    component_users_request = chromestatus_openapi.ComponentUsersRequest() # ComponentUsersRequest |  (optional)

    try:
        # Add a user to a component
        api_instance.add_user_to_component(component_id, user_id, component_users_request=component_users_request)
    except Exception as e:
        print("Exception when calling DefaultApi->add_user_to_component: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **component_id** | **int**| Component ID | 
 **user_id** | **int**| User ID | 
 **component_users_request** | [**ComponentUsersRequest**](ComponentUsersRequest.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[XsrfToken](../README.md#XsrfToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **add_xfn_gates_to_stage**
> SuccessMessage add_xfn_gates_to_stage(feature_id, stage_id)

Add a full set of cross-functional gates to a stage.

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    stage_id = 56 # int | 

    try:
        # Add a full set of cross-functional gates to a stage.
        api_response = api_instance.add_xfn_gates_to_stage(feature_id, stage_id)
        print("The response of DefaultApi->add_xfn_gates_to_stage:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->add_xfn_gates_to_stage: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **stage_id** | **int**|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Vote set successfully |  -  |
**403** | User does not have permission. |  -  |
**404** | Feature or Stage not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **authenticate_user**
> SuccessMessage authenticate_user(sign_in_request)

Authenticate user with Google Sign-In

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.sign_in_request import SignInRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    sign_in_request = chromestatus_openapi.SignInRequest() # SignInRequest | 

    try:
        # Authenticate user with Google Sign-In
        api_response = api_instance.authenticate_user(sign_in_request)
        print("The response of DefaultApi->authenticate_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->authenticate_user: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sign_in_request** | [**SignInRequest**](SignInRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | User authenticated successfully |  -  |
**401** | Invalid Token |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_account**
> AccountResponse create_account(create_account_request=create_account_request)

Create a new account

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.account_response import AccountResponse
from chromestatus_openapi.models.create_account_request import CreateAccountRequest
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    create_account_request = chromestatus_openapi.CreateAccountRequest() # CreateAccountRequest |  (optional)

    try:
        # Create a new account
        api_response = api_instance.create_account(create_account_request=create_account_request)
        print("The response of DefaultApi->create_account:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->create_account: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_account_request** | [**CreateAccountRequest**](CreateAccountRequest.md)|  | [optional] 

### Return type

[**AccountResponse**](AccountResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account created successfully |  -  |
**400** | Bad request or user already exists |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_origin_trial**
> SuccessMessage create_origin_trial(feature_id, stage_id, create_origin_trial_request=create_origin_trial_request)

Create a new origin trial

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.create_origin_trial_request import CreateOriginTrialRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    stage_id = 56 # int | 
    create_origin_trial_request = chromestatus_openapi.CreateOriginTrialRequest() # CreateOriginTrialRequest |  (optional)

    try:
        # Create a new origin trial
        api_response = api_instance.create_origin_trial(feature_id, stage_id, create_origin_trial_request=create_origin_trial_request)
        print("The response of DefaultApi->create_origin_trial:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->create_origin_trial: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **stage_id** | **int**|  | 
 **create_origin_trial_request** | [**CreateOriginTrialRequest**](CreateOriginTrialRequest.md)|  | [optional] 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Origin trial created successfully |  -  |
**400** | Invalid request. Possible reasons include an unapproved gate, a missing feature/stage, or validation errors. |  -  |
**404** | The specified feature or stage was not found. |  -  |
**500** | Server error, such as issues with obtaining necessary Chromium files or origin trial data. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_account**
> DeleteAccount200Response delete_account(account_id)

Delete an account

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.delete_account200_response import DeleteAccount200Response
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    account_id = 56 # int | ID of the account to delete

    try:
        # Delete an account
        api_response = api_instance.delete_account(account_id)
        print("The response of DefaultApi->delete_account:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_account: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **account_id** | **int**| ID of the account to delete | 

### Return type

[**DeleteAccount200Response**](DeleteAccount200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account deleted successfully |  -  |
**400** | Bad request |  -  |
**404** | Account not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **dismiss_cue**
> SuccessMessage dismiss_cue(dismiss_cue_request)

Dismiss a cue card for the signed-in user

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.dismiss_cue_request import DismissCueRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    dismiss_cue_request = chromestatus_openapi.DismissCueRequest() # DismissCueRequest | 

    try:
        # Dismiss a cue card for the signed-in user
        api_response = api_instance.dismiss_cue(dismiss_cue_request)
        print("The response of DefaultApi->dismiss_cue:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->dismiss_cue: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dismiss_cue_request** | [**DismissCueRequest**](DismissCueRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cue dismissed successfully |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **extend_origin_trial**
> SuccessMessage extend_origin_trial(feature_id, extension_stage_id)

Extend an existing origin trial

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    extension_stage_id = 56 # int | 

    try:
        # Extend an existing origin trial
        api_response = api_instance.extend_origin_trial(feature_id, extension_stage_id)
        print("The response of DefaultApi->extend_origin_trial:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->extend_origin_trial: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **extension_stage_id** | **int**|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Origin trial extended successfully |  -  |
**400** | Invalid request. Possible reasons include missing or incorrect feature/stage, or validation errors. |  -  |
**404** | The specified feature or stage was not found. |  -  |
**500** | Server error, such as issues with the origin trials API or Chromium schedule. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dismissed_cues**
> List[str] get_dismissed_cues()

Get dismissed cues for the current user

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get dismissed cues for the current user
        api_response = api_instance.get_dismissed_cues()
        print("The response of DefaultApi->get_dismissed_cues:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_dismissed_cues: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**List[str]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of dismissed cue cards |  -  |
**400** | Invalid cue provided |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feature_comments**
> GetCommentsResponse get_feature_comments(feature_id)

Get all comments for a given feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_comments_response import GetCommentsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 

    try:
        # Get all comments for a given feature
        api_response = api_instance.get_feature_comments(feature_id)
        print("The response of DefaultApi->get_feature_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_comments: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 

### Return type

[**GetCommentsResponse**](GetCommentsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of comments for the feature. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feature_links**
> FeatureLinksResponse get_feature_links(feature_id=feature_id, update_stale_links=update_stale_links)

Get feature links by feature_id

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.feature_links_response import FeatureLinksResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int |  (optional)
    update_stale_links = True # bool |  (optional) (default to True)

    try:
        # Get feature links by feature_id
        api_response = api_instance.get_feature_links(feature_id=feature_id, update_stale_links=update_stale_links)
        print("The response of DefaultApi->get_feature_links:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_links: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | [optional] 
 **update_stale_links** | **bool**|  | [optional] [default to True]

### Return type

[**FeatureLinksResponse**](FeatureLinksResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | return the links and its information to the client |  -  |
**400** | missing feature_id |  -  |
**404** | feature not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feature_links_samples**
> FeatureLinksSample get_feature_links_samples(domain=domain, type=type, is_error=is_error)

Get feature links samples

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.feature_links_sample import FeatureLinksSample
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    domain = 'domain_example' # str |  (optional)
    type = 'type_example' # str |  (optional)
    is_error = True # bool |  (optional)

    try:
        # Get feature links samples
        api_response = api_instance.get_feature_links_samples(domain=domain, type=type, is_error=is_error)
        print("The response of DefaultApi->get_feature_links_samples:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_links_samples: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **domain** | **str**|  | [optional] 
 **type** | **str**|  | [optional] 
 **is_error** | **bool**|  | [optional] 

### Return type

[**FeatureLinksSample**](FeatureLinksSample.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | return the sample links to the client |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feature_links_summary**
> FeatureLinksSummaryResponse get_feature_links_summary()

Get feature links summary

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.feature_links_summary_response import FeatureLinksSummaryResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get feature links summary
        api_response = api_instance.get_feature_links_summary()
        print("The response of DefaultApi->get_feature_links_summary:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_links_summary: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**FeatureLinksSummaryResponse**](FeatureLinksSummaryResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | return the links and its information to the client |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_gate_comments**
> List[Activity] get_gate_comments(feature_id, gate_id)

Get all comments for a given gate

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.activity import Activity
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    gate_id = 56 # int | 

    try:
        # Get all comments for a given gate
        api_response = api_instance.get_gate_comments(feature_id, gate_id)
        print("The response of DefaultApi->get_gate_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_gate_comments: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **gate_id** | **int**|  | 

### Return type

[**List[Activity]**](Activity.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of comments for the gate. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_gates_for_feature**
> GetGateResponse get_gates_for_feature(feature_id)

Get all gates for a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_gate_response import GetGateResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | The ID of the feature to retrieve votes for.

    try:
        # Get all gates for a feature
        api_response = api_instance.get_gates_for_feature(feature_id)
        print("The response of DefaultApi->get_gates_for_feature:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_gates_for_feature: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| The ID of the feature to retrieve votes for. | 

### Return type

[**GetGateResponse**](GetGateResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of gates for the specified feature. List can be empty. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_intent_body**
> GetIntentResponse get_intent_body(feature_id, stage_id, gate_id)

Get the HTML body of an intent draft

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_intent_response import GetIntentResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | Feature ID
    stage_id = 56 # int | Stage ID
    gate_id = 56 # int | Gate ID

    try:
        # Get the HTML body of an intent draft
        api_response = api_instance.get_intent_body(feature_id, stage_id, gate_id)
        print("The response of DefaultApi->get_intent_body:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_intent_body: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| Feature ID | 
 **stage_id** | **int**| Stage ID | 
 **gate_id** | **int**| Gate ID | 

### Return type

[**GetIntentResponse**](GetIntentResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json:

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Intent draft body. |  -  |
**400** | No feature or stage ID specified. |  -  |
**404** | Feature or stage not found based on given ID. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_origin_trials**
> GetOriginTrialsResponse get_origin_trials()

Get origin trials

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_origin_trials_response import GetOriginTrialsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get origin trials
        api_response = api_instance.get_origin_trials()
        print("The response of DefaultApi->get_origin_trials:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_origin_trials: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetOriginTrialsResponse**](GetOriginTrialsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of all origin trials |  -  |
**500** | Error obtaining origin trial data from API or Malformed response from origin trials API |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_pending_gates**
> GetGateResponse get_pending_gates()

Get all pending gates

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_gate_response import GetGateResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get all pending gates
        api_response = api_instance.get_pending_gates()
        print("The response of DefaultApi->get_pending_gates:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_pending_gates: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetGateResponse**](GetGateResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of all pending gates. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_process**
> Process get_process(feature_id)

Get the process for a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.process import Process
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | Feature ID

    try:
        # Get the process for a feature
        api_response = api_instance.get_process(feature_id)
        print("The response of DefaultApi->get_process:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_process: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| Feature ID | 

### Return type

[**Process**](Process.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | The process for the feature |  -  |
**404** | Feature not found based on given ID. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_progress**
> Dict[str, object] get_progress(feature_id)

Get the progress for a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | Feature ID

    try:
        # Get the progress for a feature
        api_response = api_instance.get_progress(feature_id)
        print("The response of DefaultApi->get_progress:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_progress: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| Feature ID | 

### Return type

**Dict[str, object]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | The progress for the feature. Since there&#39;s no fixed data structure for progress, it&#39;s defined as a free-form object. |  -  |
**404** | Feature not found based on given ID. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_stars**
> List[GetStarsResponse] get_stars()

Get a list of all starred feature IDs for the signed-in user

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_stars_response import GetStarsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get a list of all starred feature IDs for the signed-in user
        api_response = api_instance.get_stars()
        print("The response of DefaultApi->get_stars:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_stars: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[GetStarsResponse]**](GetStarsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of starred feature IDs |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_permissions**
> PermissionsResponse get_user_permissions(return_paired_user=return_paired_user)

Get the permissions and email of the user

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.permissions_response import PermissionsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    return_paired_user = True # bool | If true, return the permissions of the paired user. (optional)

    try:
        # Get the permissions and email of the user
        api_response = api_instance.get_user_permissions(return_paired_user=return_paired_user)
        print("The response of DefaultApi->get_user_permissions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_permissions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **return_paired_user** | **bool**| If true, return the permissions of the paired user. | [optional] 

### Return type

[**PermissionsResponse**](PermissionsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | The permissions and email of the user. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_settings**
> GetSettingsResponse get_user_settings()

Get user settings

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_settings_response import GetSettingsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Get user settings
        api_response = api_instance.get_user_settings()
        print("The response of DefaultApi->get_user_settings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_settings: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetSettingsResponse**](GetSettingsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfuly retrieved user settings |  -  |
**404** | User preference not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_votes_for_feature**
> GetVotesResponse get_votes_for_feature(feature_id)

Get votes for a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_votes_response import GetVotesResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | Feature ID

    try:
        # Get votes for a feature
        api_response = api_instance.get_votes_for_feature(feature_id)
        print("The response of DefaultApi->get_votes_for_feature:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_votes_for_feature: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| Feature ID | 

### Return type

[**GetVotesResponse**](GetVotesResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of votes for the specified feature. |  -  |
**404** | Feature not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_votes_for_feature_and_gate**
> GetVotesResponse get_votes_for_feature_and_gate(feature_id, gate_id)

Get votes for a feature and gate

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.get_votes_response import GetVotesResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | The ID of the feature to retrieve votes for.
    gate_id = 56 # int | The ID of the gate associated with the votes.

    try:
        # Get votes for a feature and gate
        api_response = api_instance.get_votes_for_feature_and_gate(feature_id, gate_id)
        print("The response of DefaultApi->get_votes_for_feature_and_gate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_votes_for_feature_and_gate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| The ID of the feature to retrieve votes for. | 
 **gate_id** | **int**| The ID of the gate associated with the votes. | 

### Return type

[**GetVotesResponse**](GetVotesResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of votes for the specified feature and gate. |  -  |
**404** | Feature or gate not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_component_users**
> ComponentsUsersResponse list_component_users()

List all components and possible users

### Example

* Api Key Authentication (XsrfToken):

```python
import chromestatus_openapi
from chromestatus_openapi.models.components_users_response import ComponentsUsersResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: XsrfToken
configuration.api_key['XsrfToken'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['XsrfToken'] = 'Bearer'

# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # List all components and possible users
        api_response = api_instance.list_component_users()
        print("The response of DefaultApi->list_component_users:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_component_users: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ComponentsUsersResponse**](ComponentsUsersResponse.md)

### Authorization

[XsrfToken](../README.md#XsrfToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of all the potential users and components with existing subscribers and owners. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_external_reviews**
> ExternalReviewsResponse list_external_reviews(review_group)

List features whose external reviews are incomplete

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.external_reviews_response import ExternalReviewsResponse
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    review_group = 'review_group_example' # str | Which review group to focus on:  * `tag` - The W3C TAG  * `gecko` - The rendering engine that powers Mozilla Firefox  * `webkit` - The rendering engine that powers Apple Safari 

    try:
        # List features whose external reviews are incomplete
        api_response = api_instance.list_external_reviews(review_group)
        print("The response of DefaultApi->list_external_reviews:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_external_reviews: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **review_group** | **str**| Which review group to focus on:  * &#x60;tag&#x60; - The W3C TAG  * &#x60;gecko&#x60; - The rendering engine that powers Mozilla Firefox  * &#x60;webkit&#x60; - The rendering engine that powers Apple Safari  | 

### Return type

[**ExternalReviewsResponse**](ExternalReviewsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of all the outstanding reviews, ordered by urgency. |  -  |
**404** | The review group wasn&#39;t recognized. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_feature_latency**
> List[FeatureLatency] list_feature_latency(start_at, end_at)

List how long each feature took to launch

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.feature_latency import FeatureLatency
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.

    try:
        # List how long each feature took to launch
        api_response = api_instance.list_feature_latency(start_at, end_at)
        print("The response of DefaultApi->list_feature_latency:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_feature_latency: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 

### Return type

[**List[FeatureLatency]**](FeatureLatency.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List the latency of features that launched in date range. |  -  |
**400** | One of the query parameters isn&#39;t a valid date in ISO YYYY-MM-DD format. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_reviews_with_latency**
> List[ReviewLatency] list_reviews_with_latency()

List recently reviewed features and their review latency

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.review_latency import ReviewLatency
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # List recently reviewed features and their review latency
        api_response = api_instance.list_reviews_with_latency()
        print("The response of DefaultApi->list_reviews_with_latency:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_reviews_with_latency: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ReviewLatency]**](ReviewLatency.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of recent reviews and their latency. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_spec_mentors**
> List[SpecMentor] list_spec_mentors(after=after)

List spec mentors and their activity

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.spec_mentor import SpecMentor
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    after = '2013-10-20' # date |  (optional)

    try:
        # List spec mentors and their activity
        api_response = api_instance.list_spec_mentors(after=after)
        print("The response of DefaultApi->list_spec_mentors:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_spec_mentors: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **after** | **date**|  | [optional] 

### Return type

[**List[SpecMentor]**](SpecMentor.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of all the matching spec mentors. |  -  |
**400** | The ?after query parameter isn&#39;t a valid date in ISO YYYY-MM-DD format. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout_user**
> SuccessMessage logout_user()

Log out the current user

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Log out the current user
        api_response = api_instance.logout_user()
        print("The response of DefaultApi->logout_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->logout_user: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | User logged out successfully |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_intent_to_blink_dev**
> MessageResponse post_intent_to_blink_dev(feature_id, stage_id, gate_id, post_intent_request=post_intent_request)

Submit an intent to be posted on blink-dev

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.message_response import MessageResponse
from chromestatus_openapi.models.post_intent_request import PostIntentRequest
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | Feature ID
    stage_id = 56 # int | Stage ID
    gate_id = 56 # int | Gate ID
    post_intent_request = chromestatus_openapi.PostIntentRequest() # PostIntentRequest | Gate ID and additional users to CC email to. (optional)

    try:
        # Submit an intent to be posted on blink-dev
        api_response = api_instance.post_intent_to_blink_dev(feature_id, stage_id, gate_id, post_intent_request=post_intent_request)
        print("The response of DefaultApi->post_intent_to_blink_dev:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_intent_to_blink_dev: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| Feature ID | 
 **stage_id** | **int**| Stage ID | 
 **gate_id** | **int**| Gate ID | 
 **post_intent_request** | [**PostIntentRequest**](PostIntentRequest.md)| Gate ID and additional users to CC email to. | [optional] 

### Return type

[**MessageResponse**](MessageResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Intent draft body. |  -  |
**400** | No feature or stage ID specified. |  -  |
**404** | Feature or stage not found based on given ID. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **refresh_token**
> List[ReviewLatency] refresh_token()

Refresh the XSRF token

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.review_latency import ReviewLatency
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # Refresh the XSRF token
        api_response = api_instance.refresh_token()
        print("The response of DefaultApi->refresh_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->refresh_token: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ReviewLatency]**](ReviewLatency.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfully refreshed the token. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_get_requests_login**
> reject_get_requests_login()

reject unneeded GET request without triggering Error Reporting

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # reject unneeded GET request without triggering Error Reporting
        api_instance.reject_get_requests_login()
    except Exception as e:
        print("Exception when calling DefaultApi->reject_get_requests_login: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**405** | Method Not Allowed |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_get_requests_logout**
> reject_get_requests_logout()

reject unneeded GET request without triggering Error Reporting

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)

    try:
        # reject unneeded GET request without triggering Error Reporting
        api_instance.reject_get_requests_logout()
    except Exception as e:
        print("Exception when calling DefaultApi->reject_get_requests_logout: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**405** | Method Not Allowed |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **remove_user_from_component**
> remove_user_from_component(component_id, user_id, component_users_request=component_users_request)

Remove a user from a component

### Example

* Api Key Authentication (XsrfToken):

```python
import chromestatus_openapi
from chromestatus_openapi.models.component_users_request import ComponentUsersRequest
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: XsrfToken
configuration.api_key['XsrfToken'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['XsrfToken'] = 'Bearer'

# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    component_id = 56 # int | Component ID
    user_id = 56 # int | User ID
    component_users_request = chromestatus_openapi.ComponentUsersRequest() # ComponentUsersRequest |  (optional)

    try:
        # Remove a user from a component
        api_instance.remove_user_from_component(component_id, user_id, component_users_request=component_users_request)
    except Exception as e:
        print("Exception when calling DefaultApi->remove_user_from_component: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **component_id** | **int**| Component ID | 
 **user_id** | **int**| User ID | 
 **component_users_request** | [**ComponentUsersRequest**](ComponentUsersRequest.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[XsrfToken](../README.md#XsrfToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_assignees_for_gate**
> SuccessMessage set_assignees_for_gate(feature_id, gate_id, post_gate_request)

Set the assignees for a gate.

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.post_gate_request import PostGateRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | The ID of the feature to retrieve votes for.
    gate_id = 56 # int | The ID of the gate to retrieve votes for.
    post_gate_request = chromestatus_openapi.PostGateRequest() # PostGateRequest | 

    try:
        # Set the assignees for a gate.
        api_response = api_instance.set_assignees_for_gate(feature_id, gate_id, post_gate_request)
        print("The response of DefaultApi->set_assignees_for_gate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->set_assignees_for_gate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| The ID of the feature to retrieve votes for. | 
 **gate_id** | **int**| The ID of the gate to retrieve votes for. | 
 **post_gate_request** | [**PostGateRequest**](PostGateRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Assignees set successfully |  -  |
**400** | Assignee is not a reviewer |  -  |
**403** | User does not have permission. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_star**
> SuccessMessage set_star(set_star_request)

Set or clear a star on the specified feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.set_star_request import SetStarRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    set_star_request = chromestatus_openapi.SetStarRequest() # SetStarRequest | 

    try:
        # Set or clear a star on the specified feature
        api_response = api_instance.set_star(set_star_request)
        print("The response of DefaultApi->set_star:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->set_star: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **set_star_request** | [**SetStarRequest**](SetStarRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Star set or cleared successfully |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_user_settings**
> SuccessMessage set_user_settings(post_settings_request)

Set the user settings (currently only the notify_as_starrer)

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.post_settings_request import PostSettingsRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    post_settings_request = chromestatus_openapi.PostSettingsRequest() # PostSettingsRequest | 

    try:
        # Set the user settings (currently only the notify_as_starrer)
        api_response = api_instance.set_user_settings(post_settings_request)
        print("The response of DefaultApi->set_user_settings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->set_user_settings: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **post_settings_request** | [**PostSettingsRequest**](PostSettingsRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Settings updated successfully |  -  |
**403** | User not signed-in |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_vote_for_feature_and_gate**
> SuccessMessage set_vote_for_feature_and_gate(feature_id, gate_id, post_vote_request)

Set a user's vote value for the specific feature and gate.

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.post_vote_request import PostVoteRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | The ID of the feature to retrieve votes for.
    gate_id = 56 # int | The ID of the gate associated with the votes.
    post_vote_request = chromestatus_openapi.PostVoteRequest() # PostVoteRequest | 

    try:
        # Set a user's vote value for the specific feature and gate.
        api_response = api_instance.set_vote_for_feature_and_gate(feature_id, gate_id, post_vote_request)
        print("The response of DefaultApi->set_vote_for_feature_and_gate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->set_vote_for_feature_and_gate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| The ID of the feature to retrieve votes for. | 
 **gate_id** | **int**| The ID of the gate associated with the votes. | 
 **post_vote_request** | [**PostVoteRequest**](PostVoteRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Vote set successfully |  -  |
**400** | Feature or gate not found. |  -  |
**403** | User does not have permission. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_feature_comment**
> SuccessMessage update_feature_comment(feature_id, patch_comment_request)

Update a comment on a feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.patch_comment_request import PatchCommentRequest
from chromestatus_openapi.models.success_message import SuccessMessage
from chromestatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v0
# See configuration.py for a list of all supported configuration parameters.
configuration = chromestatus_openapi.Configuration(
    host = "/api/v0"
)


# Enter a context with an instance of the API client
with chromestatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = chromestatus_openapi.DefaultApi(api_client)
    feature_id = 56 # int | 
    patch_comment_request = chromestatus_openapi.PatchCommentRequest() # PatchCommentRequest | 

    try:
        # Update a comment on a feature
        api_response = api_instance.update_feature_comment(feature_id, patch_comment_request)
        print("The response of DefaultApi->update_feature_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->update_feature_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**|  | 
 **patch_comment_request** | [**PatchCommentRequest**](PatchCommentRequest.md)|  | 

### Return type

[**SuccessMessage**](SuccessMessage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Comment updated successfully |  -  |
**403** | User is not allowed to update this comment |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

