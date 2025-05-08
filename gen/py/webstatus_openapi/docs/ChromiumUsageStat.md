# ChromiumUsageStat


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**timestamp** | **datetime** | The usage timestamp | 
**usage** | **float** | Snapshot of the usage metric for the given feature  | [optional] 

## Example

```python
from webstatus_openapi.models.chromium_usage_stat import ChromiumUsageStat

# TODO update the JSON string below
json = "{}"
# create an instance of ChromiumUsageStat from a JSON string
chromium_usage_stat_instance = ChromiumUsageStat.from_json(json)
# print the JSON string representation of the object
print(ChromiumUsageStat.to_json())

# convert the object into a dict
chromium_usage_stat_dict = chromium_usage_stat_instance.to_dict()
# create an instance of ChromiumUsageStat from a dict
chromium_usage_stat_from_dict = ChromiumUsageStat.from_dict(chromium_usage_stat_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


