# SuccessMessage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.success_message import SuccessMessage

# TODO update the JSON string below
json = "{}"
# create an instance of SuccessMessage from a JSON string
success_message_instance = SuccessMessage.from_json(json)
# print the JSON string representation of the object
print(SuccessMessage.to_json())

# convert the object into a dict
success_message_dict = success_message_instance.to_dict()
# create an instance of SuccessMessage from a dict
success_message_from_dict = SuccessMessage.from_dict(success_message_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


