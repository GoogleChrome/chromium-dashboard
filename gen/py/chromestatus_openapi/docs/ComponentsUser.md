# ComponentsUser


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | 
**name** | **str** |  | 
**email** | **str** |  | 

## Example

```python
from chromestatus_openapi.models.components_user import ComponentsUser

# TODO update the JSON string below
json = "{}"
# create an instance of ComponentsUser from a JSON string
components_user_instance = ComponentsUser.from_json(json)
# print the JSON string representation of the object
print(ComponentsUser.to_json())

# convert the object into a dict
components_user_dict = components_user_instance.to_dict()
# create an instance of ComponentsUser from a dict
components_user_from_dict = ComponentsUser.from_dict(components_user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


