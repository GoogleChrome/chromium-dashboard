# BrowserReleaseFeatureMetricsPage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PageMetadata**](PageMetadata.md) |  | [optional] 
**data** | [**List[BrowserReleaseFeatureMetric]**](BrowserReleaseFeatureMetric.md) |  | 

## Example

```python
from webstatus_openapi.models.browser_release_feature_metrics_page import BrowserReleaseFeatureMetricsPage

# TODO update the JSON string below
json = "{}"
# create an instance of BrowserReleaseFeatureMetricsPage from a JSON string
browser_release_feature_metrics_page_instance = BrowserReleaseFeatureMetricsPage.from_json(json)
# print the JSON string representation of the object
print(BrowserReleaseFeatureMetricsPage.to_json())

# convert the object into a dict
browser_release_feature_metrics_page_dict = browser_release_feature_metrics_page_instance.to_dict()
# create an instance of BrowserReleaseFeatureMetricsPage from a dict
browser_release_feature_metrics_page_from_dict = BrowserReleaseFeatureMetricsPage.from_dict(browser_release_feature_metrics_page_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


