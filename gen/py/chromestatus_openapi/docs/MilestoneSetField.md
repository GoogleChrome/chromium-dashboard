# MilestoneSetField


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**desktop_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**desktop_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**android_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**android_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ios_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ios_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**webview_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**webview_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.milestone_set_field import MilestoneSetField

# TODO update the JSON string below
json = "{}"
# create an instance of MilestoneSetField from a JSON string
milestone_set_field_instance = MilestoneSetField.from_json(json)
# print the JSON string representation of the object
print(MilestoneSetField.to_json())

# convert the object into a dict
milestone_set_field_dict = milestone_set_field_instance.to_dict()
# create an instance of MilestoneSetField from a dict
milestone_set_field_from_dict = MilestoneSetField.from_dict(milestone_set_field_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


