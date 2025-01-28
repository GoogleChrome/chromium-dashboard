# FeatureMetadata


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**can_i_use** | [**CanIUseInfo**](CanIUseInfo.md) |  | [optional] 
**description** | **str** |  | [optional] 

## Example

```python
from webstatus_openapi.models.feature_metadata import FeatureMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureMetadata from a JSON string
feature_metadata_instance = FeatureMetadata.from_json(json)
# print the JSON string representation of the object
print(FeatureMetadata.to_json())

# convert the object into a dict
feature_metadata_dict = feature_metadata_instance.to_dict()
# create an instance of FeatureMetadata from a dict
feature_metadata_from_dict = FeatureMetadata.from_dict(feature_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


