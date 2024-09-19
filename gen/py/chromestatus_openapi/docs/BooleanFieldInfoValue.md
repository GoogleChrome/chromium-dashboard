# BooleanFieldInfoValue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form_field_name** | **str** |  | [optional] 
**value_type** | **str** |  | [optional] 
**value** | **bool** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.boolean_field_info_value import BooleanFieldInfoValue

# TODO update the JSON string below
json = "{}"
# create an instance of BooleanFieldInfoValue from a JSON string
boolean_field_info_value_instance = BooleanFieldInfoValue.from_json(json)
# print the JSON string representation of the object
print(BooleanFieldInfoValue.to_json())

# convert the object into a dict
boolean_field_info_value_dict = boolean_field_info_value_instance.to_dict()
# create an instance of BooleanFieldInfoValue from a dict
boolean_field_info_value_from_dict = BooleanFieldInfoValue.from_dict(boolean_field_info_value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


