# PostSettingsRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**notify** | **bool** |  | 

## Example

```python
from chromestatus_openapi.models.post_settings_request import PostSettingsRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostSettingsRequest from a JSON string
post_settings_request_instance = PostSettingsRequest.from_json(json)
# print the JSON string representation of the object
print(PostSettingsRequest.to_json())

# convert the object into a dict
post_settings_request_dict = post_settings_request_instance.to_dict()
# create an instance of PostSettingsRequest from a dict
post_settings_request_from_dict = PostSettingsRequest.from_dict(post_settings_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


