# Amendment


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**field_name** | **str** |  | 
**old_value** | **str** |  | 
**new_value** | **str** |  | 

## Example

```python
from chromestatus_openapi.models.amendment import Amendment

# TODO update the JSON string below
json = "{}"
# create an instance of Amendment from a JSON string
amendment_instance = Amendment.from_json(json)
# print the JSON string representation of the object
print(Amendment.to_json())

# convert the object into a dict
amendment_dict = amendment_instance.to_dict()
# create an instance of Amendment from a dict
amendment_from_dict = Amendment.from_dict(amendment_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


