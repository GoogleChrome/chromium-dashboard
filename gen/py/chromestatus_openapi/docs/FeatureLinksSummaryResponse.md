# FeatureLinksSummaryResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_count** | **int** |  | [optional] 
**covered_count** | **int** |  | [optional] 
**uncovered_count** | **int** |  | [optional] 
**error_count** | **int** |  | [optional] 
**http_error_count** | **int** |  | [optional] 
**link_types** | [**List[CounterEntry]**](CounterEntry.md) |  | [optional] 
**uncovered_link_domains** | [**List[CounterEntry]**](CounterEntry.md) |  | [optional] 
**error_link_domains** | [**List[CounterEntry]**](CounterEntry.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_links_summary_response import FeatureLinksSummaryResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureLinksSummaryResponse from a JSON string
feature_links_summary_response_instance = FeatureLinksSummaryResponse.from_json(json)
# print the JSON string representation of the object
print(FeatureLinksSummaryResponse.to_json())

# convert the object into a dict
feature_links_summary_response_dict = feature_links_summary_response_instance.to_dict()
# create an instance of FeatureLinksSummaryResponse from a dict
feature_links_summary_response_from_dict = FeatureLinksSummaryResponse.from_dict(feature_links_summary_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


