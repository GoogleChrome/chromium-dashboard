# CanIUseInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[CanIUseItem]**](CanIUseItem.md) |  | [optional] 

## Example

```python
from webstatus_openapi.models.can_i_use_info import CanIUseInfo

# TODO update the JSON string below
json = "{}"
# create an instance of CanIUseInfo from a JSON string
can_i_use_info_instance = CanIUseInfo.from_json(json)
# print the JSON string representation of the object
print(CanIUseInfo.to_json())

# convert the object into a dict
can_i_use_info_dict = can_i_use_info_instance.to_dict()
# create an instance of CanIUseInfo from a dict
can_i_use_info_from_dict = CanIUseInfo.from_dict(can_i_use_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


