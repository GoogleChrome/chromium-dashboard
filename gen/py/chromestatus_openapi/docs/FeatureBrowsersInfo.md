# FeatureBrowsersInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chrome** | [**FeatureDictInnerChromeBrowserInfo**](FeatureDictInnerChromeBrowserInfo.md) |  | [optional] 
**ff** | [**FeatureDictInnerSingleBrowserInfo**](FeatureDictInnerSingleBrowserInfo.md) |  | [optional] 
**safari** | [**FeatureDictInnerSingleBrowserInfo**](FeatureDictInnerSingleBrowserInfo.md) |  | [optional] 
**webdev** | [**FeatureDictInnerSingleBrowserInfo**](FeatureDictInnerSingleBrowserInfo.md) |  | [optional] 
**other** | [**FeatureDictInnerSingleBrowserInfo**](FeatureDictInnerSingleBrowserInfo.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_browsers_info import FeatureBrowsersInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureBrowsersInfo from a JSON string
feature_browsers_info_instance = FeatureBrowsersInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureBrowsersInfo.to_json())

# convert the object into a dict
feature_browsers_info_dict = feature_browsers_info_instance.to_dict()
# create an instance of FeatureBrowsersInfo from a dict
feature_browsers_info_from_dict = FeatureBrowsersInfo.from_dict(feature_browsers_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


