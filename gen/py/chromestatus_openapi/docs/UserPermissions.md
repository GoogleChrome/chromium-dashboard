# UserPermissions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**can_create_feature** | **bool** |  | 
**approvable_gate_types** | **List[int]** | each element should be unique as OAS does not support set | 
**can_comment** | **bool** |  | 
**can_edit_all** | **bool** |  | 
**is_admin** | **bool** |  | 
**email** | **str** |  | 
**editable_features** | **List[int]** |  | 

## Example

```python
from chromestatus_openapi.models.user_permissions import UserPermissions

# TODO update the JSON string below
json = "{}"
# create an instance of UserPermissions from a JSON string
user_permissions_instance = UserPermissions.from_json(json)
# print the JSON string representation of the object
print(UserPermissions.to_json())

# convert the object into a dict
user_permissions_dict = user_permissions_instance.to_dict()
# create an instance of UserPermissions from a dict
user_permissions_from_dict = UserPermissions.from_dict(user_permissions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


