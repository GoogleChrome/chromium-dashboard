# FeatureDictInnerUserEditInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**by** | **str** |  | [optional] 
**when** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_user_edit_info import FeatureDictInnerUserEditInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerUserEditInfo from a JSON string
feature_dict_inner_user_edit_info_instance = FeatureDictInnerUserEditInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerUserEditInfo.to_json())

# convert the object into a dict
feature_dict_inner_user_edit_info_dict = feature_dict_inner_user_edit_info_instance.to_dict()
# create an instance of FeatureDictInnerUserEditInfo from a dict
feature_dict_inner_user_edit_info_from_dict = FeatureDictInnerUserEditInfo.from_dict(feature_dict_inner_user_edit_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


