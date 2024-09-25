# IntegerFieldInfoValue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form_field_name** | **str** |  | [optional] 
**value_type** | **str** |  | [optional] 
**value** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.integer_field_info_value import IntegerFieldInfoValue

# TODO update the JSON string below
json = "{}"
# create an instance of IntegerFieldInfoValue from a JSON string
integer_field_info_value_instance = IntegerFieldInfoValue.from_json(json)
# print the JSON string representation of the object
print(IntegerFieldInfoValue.to_json())

# convert the object into a dict
integer_field_info_value_dict = integer_field_info_value_instance.to_dict()
# create an instance of IntegerFieldInfoValue from a dict
integer_field_info_value_from_dict = IntegerFieldInfoValue.from_dict(integer_field_info_value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


