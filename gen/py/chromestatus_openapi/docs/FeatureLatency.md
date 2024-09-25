# FeatureLatency


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature** | [**FeatureLink**](FeatureLink.md) |  | 
**entry_created_date** | **str** |  | 
**shipped_milestone** | **int** |  | 
**shipped_date** | **str** |  | 
**owner_emails** | **List[str]** |  | 

## Example

```python
from chromestatus_openapi.models.feature_latency import FeatureLatency

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureLatency from a JSON string
feature_latency_instance = FeatureLatency.from_json(json)
# print the JSON string representation of the object
print(FeatureLatency.to_json())

# convert the object into a dict
feature_latency_dict = feature_latency_instance.to_dict()
# create an instance of FeatureLatency from a dict
feature_latency_from_dict = FeatureLatency.from_dict(feature_latency_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


