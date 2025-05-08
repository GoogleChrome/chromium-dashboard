# BrowserReleaseFeatureMetric


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**timestamp** | **datetime** | The timestamp that correlates to an event that may influence the count of features for a browser. This may be the release of the browser itself (when a browser may support a new set of features), or the release of another browser (when another browser supports a feature but our specified browser is now lagging behind with a new feature). Refer to the individual endpoint for more context on the use of this component.  | 
**count** | **int** | Total count of features. | [optional] 

## Example

```python
from webstatus_openapi.models.browser_release_feature_metric import BrowserReleaseFeatureMetric

# TODO update the JSON string below
json = "{}"
# create an instance of BrowserReleaseFeatureMetric from a JSON string
browser_release_feature_metric_instance = BrowserReleaseFeatureMetric.from_json(json)
# print the JSON string representation of the object
print(BrowserReleaseFeatureMetric.to_json())

# convert the object into a dict
browser_release_feature_metric_dict = browser_release_feature_metric_instance.to_dict()
# create an instance of BrowserReleaseFeatureMetric from a dict
browser_release_feature_metric_from_dict = BrowserReleaseFeatureMetric.from_dict(browser_release_feature_metric_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


