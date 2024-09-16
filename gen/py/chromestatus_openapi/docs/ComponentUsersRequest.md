# ComponentUsersRequest

Traits about the user in relation to the component

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**owner** | **bool** | Impacts this user&#39;s ownership. For PUT, add ownership. For DELETE, remove ownership. | [optional] 

## Example

```python
from chromestatus_openapi.models.component_users_request import ComponentUsersRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ComponentUsersRequest from a JSON string
component_users_request_instance = ComponentUsersRequest.from_json(json)
# print the JSON string representation of the object
print(ComponentUsersRequest.to_json())

# convert the object into a dict
component_users_request_dict = component_users_request_instance.to_dict()
# create an instance of ComponentUsersRequest from a dict
component_users_request_from_dict = ComponentUsersRequest.from_dict(component_users_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


