# FeatureDictInnerChromeBrowserInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bug** | **str** |  | [optional] 
**blink_components** | **List[str]** |  | [optional] 
**devrel** | **List[str]** |  | [optional] 
**owners** | **List[str]** |  | [optional] 
**origintrial** | **bool** |  | [optional] 
**intervention** | **bool** |  | [optional] 
**prefixed** | **bool** |  | [optional] 
**flag** | **str** |  | [optional] 
**status** | [**FeatureDictInnerBrowserStatus**](FeatureDictInnerBrowserStatus.md) |  | [optional] 
**desktop** | **int** |  | [optional] 
**android** | **int** |  | [optional] 
**webview** | **int** |  | [optional] 
**ios** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_dict_inner_chrome_browser_info import FeatureDictInnerChromeBrowserInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureDictInnerChromeBrowserInfo from a JSON string
feature_dict_inner_chrome_browser_info_instance = FeatureDictInnerChromeBrowserInfo.from_json(json)
# print the JSON string representation of the object
print(FeatureDictInnerChromeBrowserInfo.to_json())

# convert the object into a dict
feature_dict_inner_chrome_browser_info_dict = feature_dict_inner_chrome_browser_info_instance.to_dict()
# create an instance of FeatureDictInnerChromeBrowserInfo from a dict
feature_dict_inner_chrome_browser_info_from_dict = FeatureDictInnerChromeBrowserInfo.from_dict(feature_dict_inner_chrome_browser_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


