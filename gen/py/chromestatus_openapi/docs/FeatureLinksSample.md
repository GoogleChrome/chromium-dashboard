# FeatureLinksSample


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | **object** |  | 
**http_error_code** | **int** |  | 
**feature_ids** | **List[int]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_links_sample import FeatureLinksSample

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureLinksSample from a JSON string
feature_links_sample_instance = FeatureLinksSample.from_json(json)
# print the JSON string representation of the object
print(FeatureLinksSample.to_json())

# convert the object into a dict
feature_links_sample_dict = feature_links_sample_instance.to_dict()
# create an instance of FeatureLinksSample from a dict
feature_links_sample_from_dict = FeatureLinksSample.from_dict(feature_links_sample_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


