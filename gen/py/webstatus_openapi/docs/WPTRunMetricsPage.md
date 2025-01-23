# WPTRunMetricsPage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PageMetadata**](PageMetadata.md) |  | [optional] 
**data** | [**List[WPTRunMetric]**](WPTRunMetric.md) |  | 

## Example

```python
from webstatus_openapi.models.wpt_run_metrics_page import WPTRunMetricsPage

# TODO update the JSON string below
json = "{}"
# create an instance of WPTRunMetricsPage from a JSON string
wpt_run_metrics_page_instance = WPTRunMetricsPage.from_json(json)
# print the JSON string representation of the object
print(WPTRunMetricsPage.to_json())

# convert the object into a dict
wpt_run_metrics_page_dict = wpt_run_metrics_page_instance.to_dict()
# create an instance of WPTRunMetricsPage from a dict
wpt_run_metrics_page_from_dict = WPTRunMetricsPage.from_dict(wpt_run_metrics_page_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


