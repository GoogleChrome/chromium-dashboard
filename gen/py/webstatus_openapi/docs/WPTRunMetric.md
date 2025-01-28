# WPTRunMetric


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_timestamp** | **datetime** | The start timestamp of the run. | 
**total_tests_count** | **int** | Total number of tests | [optional] 
**test_pass_count** | **int** | Number of passing tests | [optional] 

## Example

```python
from webstatus_openapi.models.wpt_run_metric import WPTRunMetric

# TODO update the JSON string below
json = "{}"
# create an instance of WPTRunMetric from a JSON string
wpt_run_metric_instance = WPTRunMetric.from_json(json)
# print the JSON string representation of the object
print(WPTRunMetric.to_json())

# convert the object into a dict
wpt_run_metric_dict = wpt_run_metric_instance.to_dict()
# create an instance of WPTRunMetric from a dict
wpt_run_metric_from_dict = WPTRunMetric.from_dict(wpt_run_metric_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


