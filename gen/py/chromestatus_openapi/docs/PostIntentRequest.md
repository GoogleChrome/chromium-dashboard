# PostIntentRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**gate_id** | **int** |  | 
**intent_cc_emails** | **List[str]** |  | 

## Example

```python
from chromestatus_openapi.models.post_intent_request import PostIntentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostIntentRequest from a JSON string
post_intent_request_instance = PostIntentRequest.from_json(json)
# print the JSON string representation of the object
print(PostIntentRequest.to_json())

# convert the object into a dict
post_intent_request_dict = post_intent_request_instance.to_dict()
# create an instance of PostIntentRequest from a dict
post_intent_request_from_dict = PostIntentRequest.from_dict(post_intent_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


