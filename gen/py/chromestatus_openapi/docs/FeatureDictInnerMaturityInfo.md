# FeatureDictInnerMaturityInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | [optional] 
**short_text** | **str** |  | [optional] 
**val** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_maturity_info import FeatureDictInnerMaturityInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerMaturityInfo from a JSON string
feature_dict_inner_maturity_info_instance = FeatureDictInnerMaturityInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerMaturityInfo.to_json())

# convert the object into a dict
feature_dict_inner_maturity_info_dict = feature_dict_inner_maturity_info_instance.to_dict()
# create an instance of FeatureDictInnerMaturityInfo from a dict
feature_dict_inner_maturity_info_from_dict = FeatureDictInnerMaturityInfo.from_dict(feature_dict_inner_maturity_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


