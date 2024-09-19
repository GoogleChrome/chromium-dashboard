# PostGateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**assignees** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.post_gate_request import PostGateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostGateRequest from a JSON string
post_gate_request_instance = PostGateRequest.from_json(json)
# print the JSON string representation of the object
print(PostGateRequest.to_json())

# convert the object into a dict
post_gate_request_dict = post_gate_request_instance.to_dict()
# create an instance of PostGateRequest from a dict
post_gate_request_from_dict = PostGateRequest.from_dict(post_gate_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


