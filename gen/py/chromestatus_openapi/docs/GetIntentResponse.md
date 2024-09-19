# GetIntentResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** |  | 
**email_body** | **str** |  | 

## Example

```python
from chromestatus_openapi.models.get_intent_response import GetIntentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetIntentResponse from a JSON string
get_intent_response_instance = GetIntentResponse.from_json(json)
# print the JSON string representation of the object
print(GetIntentResponse.to_json())

# convert the object into a dict
get_intent_response_dict = get_intent_response_instance.to_dict()
# create an instance of GetIntentResponse from a dict
get_intent_response_from_dict = GetIntentResponse.from_dict(get_intent_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


