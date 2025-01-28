# FeatureSpecInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**links** | [**List[SpecLink]**](SpecLink.md) |  | [optional] 

## Example

```python
from webstatus_openapi.models.feature_spec_info import FeatureSpecInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureSpecInfo from a JSON string
feature_spec_info_instance = FeatureSpecInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureSpecInfo.to_json())

# convert the object into a dict
feature_spec_info_dict = feature_spec_info_instance.to_dict()
# create an instance of FeatureSpecInfo from a dict
feature_spec_info_from_dict = FeatureSpecInfo.from_dict(feature_spec_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


