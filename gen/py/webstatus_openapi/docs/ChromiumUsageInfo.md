# ChromiumUsageInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**daily** | **float** | Latest snapshot of the usage metric for the given feature.  | [optional] 

## Example

```python
from webstatus_openapi.models.chromium_usage_info import ChromiumUsageInfo

# TODO update the JSON string below
json = "{}"
# create an instance of ChromiumUsageInfo from a JSON string
chromium_usage_info_instance = ChromiumUsageInfo.from_json(json)
# print the JSON string representation of the object
print(ChromiumUsageInfo.to_json())

# convert the object into a dict
chromium_usage_info_dict = chromium_usage_info_instance.to_dict()
# create an instance of ChromiumUsageInfo from a dict
chromium_usage_info_from_dict = ChromiumUsageInfo.from_dict(chromium_usage_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


