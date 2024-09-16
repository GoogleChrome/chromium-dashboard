# FeatureDictInnerBrowserStatus


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | [optional] 
**val** | **int** |  | [optional] 
**milestone_str** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_browser_status import FeatureDictInnerBrowserStatus

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerBrowserStatus from a JSON string
feature_dict_inner_browser_status_instance = FeatureDictInnerBrowserStatus.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerBrowserStatus.to_json())

# convert the object into a dict
feature_dict_inner_browser_status_dict = feature_dict_inner_browser_status_instance.to_dict()
# create an instance of FeatureDictInnerBrowserStatus from a dict
feature_dict_inner_browser_status_from_dict = FeatureDictInnerBrowserStatus.from_dict(feature_dict_inner_browser_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


