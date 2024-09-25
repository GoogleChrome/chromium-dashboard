# ComponentsUsersResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**users** | [**List[ComponentsUser]**](ComponentsUser.md) |  | [optional] 
**components** | [**List[OwnersAndSubscribersOfComponent]**](OwnersAndSubscribersOfComponent.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.components_users_response import ComponentsUsersResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ComponentsUsersResponse from a JSON string
components_users_response_instance = ComponentsUsersResponse.from_json(json)
# print the JSON string representation of the object
print(ComponentsUsersResponse.to_json())

# convert the object into a dict
components_users_response_dict = components_users_response_instance.to_dict()
# create an instance of ComponentsUsersResponse from a dict
components_users_response_from_dict = ComponentsUsersResponse.from_dict(components_users_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


