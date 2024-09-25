# FeatureLink


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | 
**name** | **str** |  | 

## Example

```python
from chromestatus_openapi.models.feature_link import FeatureLink

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureLink from a JSON string
feature_link_instance = FeatureLink.from_json(json)
# print the JSON string representation of the object
print(FeatureLink.to_json())

# convert the object into a dict
feature_link_dict = feature_link_instance.to_dict()
# create an instance of FeatureLink from a dict
feature_link_from_dict = FeatureLink.from_dict(feature_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


