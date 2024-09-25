# ProgressItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**field** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.progress_item import ProgressItem

# TODO update the JSON string below
json = "{}"
# create an instance of ProgressItem from a JSON string
progress_item_instance = ProgressItem.from_json(json)
# print the JSON string representation of the object
print(ProgressItem.to_json())

# convert the object into a dict
progress_item_dict = progress_item_instance.to_dict()
# create an instance of ProgressItem from a dict
progress_item_from_dict = ProgressItem.from_dict(progress_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


