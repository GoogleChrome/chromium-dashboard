# chromestatus_openapi.DefaultApi

All URIs are relative to */api/v0*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_user_to_component**](DefaultApi.md#add_user_to_component) | **PUT** /components/{componentId}/users/{userId} | Add a user to a component
[**create_account**](DefaultApi.md#create_account) | **POST** /accounts | Create a new account
[**delete_account**](DefaultApi.md#delete_account) | **DELETE** /accounts/{account_id} | Delete an account
[**dismiss_cue**](DefaultApi.md#dismiss_cue) | **POST** /currentuser/cues | Dismiss a cue card for the signed-in user
[**get_all_features**](DefaultApi.md#get_all_features) | **GET** /features | retrive a list of feature
[**get_dismissed_cues**](DefaultApi.md#get_dismissed_cues) | **GET** /currentuser/cues | Get dismissed cues for the current user
[**get_feature_by_id**](DefaultApi.md#get_feature_by_id) | **GET** /features/{feature_id} | Get a feature by ID
[**get_feature_links**](DefaultApi.md#get_feature_links) | **GET** /feature_links | Get feature links by feature_id
[**get_feature_links_samples**](DefaultApi.md#get_feature_links_samples) | **GET** /feature_links_samples | Get feature links samples
[**get_feature_links_summary**](DefaultApi.md#get_feature_links_summary) | **GET** /feature_links_summary | Get feature links summary
[**get_intent_body**](DefaultApi.md#get_intent_body) | **GET** /features/{feature_id}/{stage_id}/{gate_id}/intent | Get the HTML body of an intent draft
[**get_user_permissions**](DefaultApi.md#get_user_permissions) | **GET** /currentuser/permissions | Get the permissions and email of the user
[**list_component_users**](DefaultApi.md#list_component_users) | **GET** /componentsusers | List all components and possible users
[**list_external_reviews**](DefaultApi.md#list_external_reviews) | **GET** /external_reviews/{review_group} | List features whose external reviews are incomplete
[**list_feature_latency**](DefaultApi.md#list_feature_latency) | **GET** /feature-latency | List how long each feature took to launch
[**list_reviews_with_latency**](DefaultApi.md#list_reviews_with_latency) | **GET** /review-latency | List recently reviewed features and their review latency
[**list_spec_mentors**](DefaultApi.md#list_spec_mentors) | **GET** /spec_mentors | List spec mentors and their activity
[**post_intent_to_blink_dev**](DefaultApi.md#post_intent_to_blink_dev) | **POST** /features/{feature_id}/{stage_id}/{gate_id}/intent | Submit an intent to be posted on blink-dev
[**remove_user_from_component**](DefaultApi.md#remove_user_from_component) | **DELETE** /components/{componentId}/users/{userId} | Remove a user from a component


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

# **get_all_features**
> FeatureSearchResponse get_all_features(q=q, sort=sort, num=num, start=start, milestone=milestone, release_notes_milestone=release_notes_milestone)

retrive a list of feature

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.feature_search_response import FeatureSearchResponse
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
    q = 'q_example' # str | Search query string. (optional)
    sort = 'sort_example' # str | Sorting specification. (optional)
    num = 100 # int | Number of results to return. (optional) (default to 100)
    start = 0 # int | Index of the first result to return. (optional) (default to 0)
    milestone = 56 # int | Filter features by milestone. (optional)
    release_notes_milestone = 56 # int | Filter features by release notes milestone. (optional)

    try:
        # retrive a list of feature
        api_response = api_instance.get_all_features(q=q, sort=sort, num=num, start=start, milestone=milestone, release_notes_milestone=release_notes_milestone)
        print("The response of DefaultApi->get_all_features:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_all_features: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**| Search query string. | [optional] 
 **sort** | **str**| Sorting specification. | [optional] 
 **num** | **int**| Number of results to return. | [optional] [default to 100]
 **start** | **int**| Index of the first result to return. | [optional] [default to 0]
 **milestone** | **int**| Filter features by milestone. | [optional] 
 **release_notes_milestone** | **int**| Filter features by release notes milestone. | [optional] 

### Return type

[**FeatureSearchResponse**](FeatureSearchResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of features with count |  -  |

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

# **get_feature_by_id**
> VerboseFeatureDict get_feature_by_id(feature_id)

Get a feature by ID

### Example


```python
import chromestatus_openapi
from chromestatus_openapi.models.verbose_feature_dict import VerboseFeatureDict
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
    feature_id = 56 # int | ID of the feature to retrieve

    try:
        # Get a feature by ID
        api_response = api_instance.get_feature_by_id(feature_id)
        print("The response of DefaultApi->get_feature_by_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_by_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **int**| ID of the feature to retrieve | 

### Return type

[**VerboseFeatureDict**](VerboseFeatureDict.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Feature retrieved successfully |  -  |
**404** | Feature not found |  -  |

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

