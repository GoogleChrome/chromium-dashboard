# GetSettingsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**notify_as_starrer** | **bool** |  | 

## Example

```python
from chromestatus_openapi.models.get_settings_response import GetSettingsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetSettingsResponse from a JSON string
get_settings_response_instance = GetSettingsResponse.from_json(json)
# print the JSON string representation of the object
print(GetSettingsResponse.to_json())

# convert the object into a dict
get_settings_response_dict = get_settings_response_instance.to_dict()
# create an instance of GetSettingsResponse from a dict
get_settings_response_from_dict = GetSettingsResponse.from_dict(get_settings_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


