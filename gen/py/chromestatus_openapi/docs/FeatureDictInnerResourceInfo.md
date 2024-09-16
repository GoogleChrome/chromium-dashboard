# FeatureDictInnerResourceInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**samples** | **List[str]** |  | [optional] 
**docs** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_resource_info import FeatureDictInnerResourceInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerResourceInfo from a JSON string
feature_dict_inner_resource_info_instance = FeatureDictInnerResourceInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerResourceInfo.to_json())

# convert the object into a dict
feature_dict_inner_resource_info_dict = feature_dict_inner_resource_info_instance.to_dict()
# create an instance of FeatureDictInnerResourceInfo from a dict
feature_dict_inner_resource_info_from_dict = FeatureDictInnerResourceInfo.from_dict(feature_dict_inner_resource_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


