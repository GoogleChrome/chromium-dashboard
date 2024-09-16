# FeatureDictInnerViewInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | [optional] 
**val** | **int** |  | [optional] 
**url** | **str** |  | [optional] 
**notes** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_view_info import FeatureDictInnerViewInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerViewInfo from a JSON string
feature_dict_inner_view_info_instance = FeatureDictInnerViewInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerViewInfo.to_json())

# convert the object into a dict
feature_dict_inner_view_info_dict = feature_dict_inner_view_info_instance.to_dict()
# create an instance of FeatureDictInnerViewInfo from a dict
feature_dict_inner_view_info_from_dict = FeatureDictInnerViewInfo.from_dict(feature_dict_inner_view_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


