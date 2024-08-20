# PermissionsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user** | [**UserPermissions**](UserPermissions.md) |  | 

## Example

```python
from chromestatus_openapi.models.permissions_response import PermissionsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PermissionsResponse from a JSON string
permissions_response_instance = PermissionsResponse.from_json(json)
# print the JSON string representation of the object
print(PermissionsResponse.to_json())

# convert the object into a dict
permissions_response_dict = permissions_response_instance.to_dict()
# create an instance of PermissionsResponse from a dict
permissions_response_from_dict = PermissionsResponse.from_dict(permissions_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


