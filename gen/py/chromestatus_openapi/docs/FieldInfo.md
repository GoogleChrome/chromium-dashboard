# FieldInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form_field_name** | **str** |  | [optional] 
**value** | [**FieldInfoValue**](FieldInfoValue.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.field_info import FieldInfo

# TODO update the JSON string below
json = "{}"
# create an instance of FieldInfo from a JSON string
field_info_instance = FieldInfo.from_json(json)
# print the JSON string representation of the object
print(FieldInfo.to_json())

# convert the object into a dict
field_info_dict = field_info_instance.to_dict()
# create an instance of FieldInfo from a dict
field_info_from_dict = FieldInfo.from_dict(field_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


