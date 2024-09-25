# Process


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**applicability** | **str** |  | [optional] 
**stages** | [**List[ProcessStage]**](ProcessStage.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.process import Process

# TODO update the JSON string below
json = "{}"
# create an instance of Process from a JSON string
process_instance = Process.from_json(json)
# print the JSON string representation of the object
print(Process.to_json())

# convert the object into a dict
process_dict = process_instance.to_dict()
# create an instance of Process from a dict
process_from_dict = Process.from_dict(process_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


