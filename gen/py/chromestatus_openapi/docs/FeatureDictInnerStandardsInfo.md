# FeatureDictInnerStandardsInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**spec** | **str** |  | [optional] 
**maturity** | [**FeatureDictInnerMaturityInfo**](FeatureDictInnerMaturityInfo.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_standards_info import FeatureDictInnerStandardsInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerStandardsInfo from a JSON string
feature_dict_inner_standards_info_instance = FeatureDictInnerStandardsInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerStandardsInfo.to_json())

# convert the object into a dict
feature_dict_inner_standards_info_dict = feature_dict_inner_standards_info_instance.to_dict()
# create an instance of FeatureDictInnerStandardsInfo from a dict
feature_dict_inner_standards_info_from_dict = FeatureDictInnerStandardsInfo.from_dict(feature_dict_inner_standards_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


