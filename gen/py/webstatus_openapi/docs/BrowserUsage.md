# BrowserUsage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chromium** | [**ChromiumUsageInfo**](ChromiumUsageInfo.md) |  | [optional] 

## Example

```python
from webstatus_openapi.models.browser_usage import BrowserUsage

# TODO update the JSON string below
json = "{}"
# create an instance of BrowserUsage from a JSON string
browser_usage_instance = BrowserUsage.from_json(json)
# print the JSON string representation of the object
print(BrowserUsage.to_json())

# convert the object into a dict
browser_usage_dict = browser_usage_instance.to_dict()
# create an instance of BrowserUsage from a dict
browser_usage_from_dict = BrowserUsage.from_dict(browser_usage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


