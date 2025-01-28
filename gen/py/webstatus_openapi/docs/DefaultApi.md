# webstatus_openapi.DefaultApi

All URIs are relative to *https://api.webstatus.dev*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_feature**](DefaultApi.md#get_feature) | **GET** /v1/features/{feature_id} | Get Feature
[**get_feature_metadata**](DefaultApi.md#get_feature_metadata) | **GET** /v1/features/{feature_id}/feature-metadata | Get metadata for a given feature from github.com/web-platform-dx/web-features
[**get_saved_search**](DefaultApi.md#get_saved_search) | **GET** /v1/saved-searches/{search_id} | Get saved search
[**list_aggregated_feature_support**](DefaultApi.md#list_aggregated_feature_support) | **GET** /v1/stats/features/browsers/{browser}/feature_counts | Returns the count of features supported for a specified browser over time. The timestamps for the individual metrics represent the releases of the specified browser. 
[**list_aggregated_wpt_metrics**](DefaultApi.md#list_aggregated_wpt_metrics) | **GET** /v1/stats/wpt/browsers/{browser}/channels/{channel}/{metric_view} | Gets aggregated WPT test counts for a specified browser and channel. Optionally filter by feature IDs. 
[**list_chromium_daily_usage_stats**](DefaultApi.md#list_chromium_daily_usage_stats) | **GET** /v1/features/{feature_id}/stats/usage/chromium/daily_stats | Get Chromium daily usage metrics for a given feature
[**list_feature_wpt_metrics**](DefaultApi.md#list_feature_wpt_metrics) | **GET** /v1/features/{feature_id}/stats/wpt/browsers/{browser}/channels/{channel}/{metric_view} | Retrieve the wpt stats for a particular feature.
[**list_features**](DefaultApi.md#list_features) | **GET** /v1/features | List features
[**list_missing_one_implemenation_counts**](DefaultApi.md#list_missing_one_implemenation_counts) | **GET** /v1/stats/features/browsers/{browser}/missing_one_implementation_counts | Returns the count of features that are supported by all of the specified comparison browsers but not supported by the specified target browser, as of each browser&#39;s (target browser or comparison browser) release date. 
[**list_saved_searches**](DefaultApi.md#list_saved_searches) | **GET** /v1/saved-searches | List saved searches


# **get_feature**
> Feature get_feature(feature_id, wpt_metric_view=wpt_metric_view)

Get Feature

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.feature import Feature
from webstatus_openapi.models.wpt_metric_view import WPTMetricView
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    feature_id = 'feature_id_example' # str | Feature ID
    wpt_metric_view = webstatus_openapi.WPTMetricView() # WPTMetricView |  (optional)

    try:
        # Get Feature
        api_response = api_instance.get_feature(feature_id, wpt_metric_view=wpt_metric_view)
        print("The response of DefaultApi->get_feature:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **str**| Feature ID | 
 **wpt_metric_view** | [**WPTMetricView**](.md)|  | [optional] 

### Return type

[**Feature**](Feature.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feature_metadata**
> FeatureMetadata get_feature_metadata(feature_id)

Get metadata for a given feature from github.com/web-platform-dx/web-features

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.feature_metadata import FeatureMetadata
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    feature_id = 'feature_id_example' # str | Feature ID

    try:
        # Get metadata for a given feature from github.com/web-platform-dx/web-features
        api_response = api_instance.get_feature_metadata(feature_id)
        print("The response of DefaultApi->get_feature_metadata:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_feature_metadata: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **str**| Feature ID | 

### Return type

[**FeatureMetadata**](FeatureMetadata.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_saved_search**
> SavedSearchResponse get_saved_search(search_id)

Get saved search

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.saved_search_response import SavedSearchResponse
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    search_id = 'search_id_example' # str | Saved Search ID

    try:
        # Get saved search
        api_response = api_instance.get_saved_search(search_id)
        print("The response of DefaultApi->get_saved_search:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_saved_search: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search_id** | **str**| Saved Search ID | 

### Return type

[**SavedSearchResponse**](SavedSearchResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_aggregated_feature_support**
> BrowserReleaseFeatureMetricsPage list_aggregated_feature_support(browser, start_at, end_at, page_token=page_token, page_size=page_size)

Returns the count of features supported for a specified browser over time. The timestamps for the individual metrics represent the releases of the specified browser. 

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.browser_release_feature_metrics_page import BrowserReleaseFeatureMetricsPage
from webstatus_openapi.models.supported_browsers import SupportedBrowsers
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    browser = webstatus_openapi.SupportedBrowsers() # SupportedBrowsers | Browser name
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)

    try:
        # Returns the count of features supported for a specified browser over time. The timestamps for the individual metrics represent the releases of the specified browser. 
        api_response = api_instance.list_aggregated_feature_support(browser, start_at, end_at, page_token=page_token, page_size=page_size)
        print("The response of DefaultApi->list_aggregated_feature_support:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_aggregated_feature_support: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **browser** | [**SupportedBrowsers**](.md)| Browser name | 
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]

### Return type

[**BrowserReleaseFeatureMetricsPage**](BrowserReleaseFeatureMetricsPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_aggregated_wpt_metrics**
> WPTRunMetricsPage list_aggregated_wpt_metrics(browser, channel, metric_view, start_at, end_at, page_token=page_token, page_size=page_size, feature_id=feature_id)

Gets aggregated WPT test counts for a specified browser and channel. Optionally filter by feature IDs. 

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.supported_browsers import SupportedBrowsers
from webstatus_openapi.models.wpt_metric_view import WPTMetricView
from webstatus_openapi.models.wpt_run_metrics_page import WPTRunMetricsPage
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    browser = webstatus_openapi.SupportedBrowsers() # SupportedBrowsers | Browser name
    channel = 'channel_example' # str | Browser name
    metric_view = webstatus_openapi.WPTMetricView() # WPTMetricView | Specified metric view of the WPT data.
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)
    feature_id = ['feature_id_example'] # List[str] | A list of feature IDs to filter results. TThe list is provided by specifying repeating query parameters. Example: ?featureId=id1&featureId=id2  (optional)

    try:
        # Gets aggregated WPT test counts for a specified browser and channel. Optionally filter by feature IDs. 
        api_response = api_instance.list_aggregated_wpt_metrics(browser, channel, metric_view, start_at, end_at, page_token=page_token, page_size=page_size, feature_id=feature_id)
        print("The response of DefaultApi->list_aggregated_wpt_metrics:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_aggregated_wpt_metrics: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **browser** | [**SupportedBrowsers**](.md)| Browser name | 
 **channel** | **str**| Browser name | 
 **metric_view** | [**WPTMetricView**](.md)| Specified metric view of the WPT data. | 
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]
 **feature_id** | [**List[str]**](str.md)| A list of feature IDs to filter results. TThe list is provided by specifying repeating query parameters. Example: ?featureId&#x3D;id1&amp;featureId&#x3D;id2  | [optional] 

### Return type

[**WPTRunMetricsPage**](WPTRunMetricsPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_chromium_daily_usage_stats**
> ChromiumDailyStatsPage list_chromium_daily_usage_stats(feature_id, start_at, end_at, page_token=page_token, page_size=page_size)

Get Chromium daily usage metrics for a given feature

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.chromium_daily_stats_page import ChromiumDailyStatsPage
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    feature_id = 'feature_id_example' # str | Feature ID
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)

    try:
        # Get Chromium daily usage metrics for a given feature
        api_response = api_instance.list_chromium_daily_usage_stats(feature_id, start_at, end_at, page_token=page_token, page_size=page_size)
        print("The response of DefaultApi->list_chromium_daily_usage_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_chromium_daily_usage_stats: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **str**| Feature ID | 
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]

### Return type

[**ChromiumDailyStatsPage**](ChromiumDailyStatsPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_feature_wpt_metrics**
> WPTRunMetricsPage list_feature_wpt_metrics(feature_id, browser, channel, metric_view, start_at, end_at, page_token=page_token, page_size=page_size)

Retrieve the wpt stats for a particular feature.

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.supported_browsers import SupportedBrowsers
from webstatus_openapi.models.wpt_metric_view import WPTMetricView
from webstatus_openapi.models.wpt_run_metrics_page import WPTRunMetricsPage
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    feature_id = 'feature_id_example' # str | Feature ID
    browser = webstatus_openapi.SupportedBrowsers() # SupportedBrowsers | Browser name
    channel = 'channel_example' # str | Browser name
    metric_view = webstatus_openapi.WPTMetricView() # WPTMetricView | Specified metric view of the WPT data.
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)

    try:
        # Retrieve the wpt stats for a particular feature.
        api_response = api_instance.list_feature_wpt_metrics(feature_id, browser, channel, metric_view, start_at, end_at, page_token=page_token, page_size=page_size)
        print("The response of DefaultApi->list_feature_wpt_metrics:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_feature_wpt_metrics: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **feature_id** | **str**| Feature ID | 
 **browser** | [**SupportedBrowsers**](.md)| Browser name | 
 **channel** | **str**| Browser name | 
 **metric_view** | [**WPTMetricView**](.md)| Specified metric view of the WPT data. | 
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]

### Return type

[**WPTRunMetricsPage**](WPTRunMetricsPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_features**
> FeaturePage list_features(page_token=page_token, page_size=page_size, wpt_metric_view=wpt_metric_view, q=q, sort=sort)

List features

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.feature_page import FeaturePage
from webstatus_openapi.models.wpt_metric_view import WPTMetricView
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)
    wpt_metric_view = webstatus_openapi.WPTMetricView() # WPTMetricView |  (optional)
    q = 'q_example' # str | A query string to represent the filters to apply the datastore while searching. The query must follow the ANTLR grammar. Please read the query readme at antlr/FeatureSearch.md. The query must be url safe.  (optional)
    sort = 'sort_example' # str | Field to sort by, with 'asc' for ascending and 'desc' for descending order. Defaults to sorting by 'name' in ascending order (e.g., 'name_asc').  (optional)

    try:
        # List features
        api_response = api_instance.list_features(page_token=page_token, page_size=page_size, wpt_metric_view=wpt_metric_view, q=q, sort=sort)
        print("The response of DefaultApi->list_features:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_features: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]
 **wpt_metric_view** | [**WPTMetricView**](.md)|  | [optional] 
 **q** | **str**| A query string to represent the filters to apply the datastore while searching. The query must follow the ANTLR grammar. Please read the query readme at antlr/FeatureSearch.md. The query must be url safe.  | [optional] 
 **sort** | **str**| Field to sort by, with &#39;asc&#39; for ascending and &#39;desc&#39; for descending order. Defaults to sorting by &#39;name&#39; in ascending order (e.g., &#39;name_asc&#39;).  | [optional] 

### Return type

[**FeaturePage**](FeaturePage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_missing_one_implemenation_counts**
> BrowserReleaseFeatureMetricsPage list_missing_one_implemenation_counts(start_at, end_at, browser, page_token=page_token, page_size=page_size)

Returns the count of features that are supported by all of the specified comparison browsers but not supported by the specified target browser, as of each browser's (target browser or comparison browser) release date. 

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.browser_release_feature_metrics_page import BrowserReleaseFeatureMetricsPage
from webstatus_openapi.models.supported_browsers import SupportedBrowsers
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)
    start_at = '2013-10-20' # date | Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
    end_at = '2013-10-20' # date | End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
    browser = webstatus_openapi.SupportedBrowsers() # SupportedBrowsers | Browser name
    page_token = 'page_token_example' # str | Pagination token (optional)
    page_size = 1 # int | Number of results to return (optional) (default to 1)

    try:
        # Returns the count of features that are supported by all of the specified comparison browsers but not supported by the specified target browser, as of each browser's (target browser or comparison browser) release date. 
        api_response = api_instance.list_missing_one_implemenation_counts(start_at, end_at, browser, page_token=page_token, page_size=page_size)
        print("The response of DefaultApi->list_missing_one_implemenation_counts:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_missing_one_implemenation_counts: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **start_at** | **date**| Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive. | 
 **end_at** | **date**| End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive. | 
 **browser** | [**SupportedBrowsers**](.md)| Browser name | 
 **page_token** | **str**| Pagination token | [optional] 
 **page_size** | **int**| Number of results to return | [optional] [default to 1]

### Return type

[**BrowserReleaseFeatureMetricsPage**](BrowserReleaseFeatureMetricsPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Input |  -  |
**404** | Not Found |  -  |
**429** | Rate Limit |  -  |
**500** | Internal Service Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_saved_searches**
> SavedSearchPage list_saved_searches()

List saved searches

### Example


```python
import webstatus_openapi
from webstatus_openapi.models.saved_search_page import SavedSearchPage
from webstatus_openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.webstatus.dev
# See configuration.py for a list of all supported configuration parameters.
configuration = webstatus_openapi.Configuration(
    host = "https://api.webstatus.dev"
)


# Enter a context with an instance of the API client
with webstatus_openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = webstatus_openapi.DefaultApi(api_client)

    try:
        # List saved searches
        api_response = api_instance.list_saved_searches()
        print("The response of DefaultApi->list_saved_searches:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->list_saved_searches: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**SavedSearchPage**](SavedSearchPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

