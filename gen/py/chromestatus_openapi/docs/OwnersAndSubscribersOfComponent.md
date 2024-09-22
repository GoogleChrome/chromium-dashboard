# OwnersAndSubscribersOfComponent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | 
**name** | **str** |  | 
**subscriber_ids** | **List[int]** |  | [optional] 
**owner_ids** | **List[int]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.owners_and_subscribers_of_component import OwnersAndSubscribersOfComponent

# TODO update the JSON string below
json = "{}"
# create an instance of OwnersAndSubscribersOfComponent from a JSON string
owners_and_subscribers_of_component_instance = OwnersAndSubscribersOfComponent.from_json(json)
# print the JSON string representation of the object
print(OwnersAndSubscribersOfComponent.to_json())

# convert the object into a dict
owners_and_subscribers_of_component_dict = owners_and_subscribers_of_component_instance.to_dict()
# create an instance of OwnersAndSubscribersOfComponent from a dict
owners_and_subscribers_of_component_from_dict = OwnersAndSubscribersOfComponent.from_dict(owners_and_subscribers_of_component_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


