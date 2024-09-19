# ArrayFieldInfoValue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form_field_name** | **str** |  | [optional] 
**value_type** | **str** |  | [optional] 
**value** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.array_field_info_value import ArrayFieldInfoValue

# TODO update the JSON string below
json = "{}"
# create an instance of ArrayFieldInfoValue from a JSON string
array_field_info_value_instance = ArrayFieldInfoValue.from_json(json)
# print the JSON string representation of the object
print(ArrayFieldInfoValue.to_json())

# convert the object into a dict
array_field_info_value_dict = array_field_info_value_instance.to_dict()
# create an instance of ArrayFieldInfoValue from a dict
array_field_info_value_from_dict = ArrayFieldInfoValue.from_dict(array_field_info_value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


