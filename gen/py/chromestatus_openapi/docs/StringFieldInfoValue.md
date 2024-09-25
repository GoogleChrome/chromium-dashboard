# StringFieldInfoValue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form_field_name** | **str** |  | [optional] 
**value_type** | **str** |  | [optional] 
**value** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.string_field_info_value import StringFieldInfoValue

# TODO update the JSON string below
json = "{}"
# create an instance of StringFieldInfoValue from a JSON string
string_field_info_value_instance = StringFieldInfoValue.from_json(json)
# print the JSON string representation of the object
print(StringFieldInfoValue.to_json())

# convert the object into a dict
string_field_info_value_dict = string_field_info_value_instance.to_dict()
# create an instance of StringFieldInfoValue from a dict
string_field_info_value_from_dict = StringFieldInfoValue.from_dict(string_field_info_value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


