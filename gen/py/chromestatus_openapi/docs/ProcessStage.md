# ProcessStage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**progress_items** | [**List[ProgressItem]**](ProgressItem.md) |  | [optional] 
**actions** | [**List[Action]**](Action.md) |  | [optional] 
**approvals** | [**List[GateInfo]**](GateInfo.md) |  | [optional] 
**incoming_stage** | **int** |  | [optional] 
**outgoing_stage** | **int** |  | [optional] 
**stage_type** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.process_stage import ProcessStage

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessStage from a JSON string
process_stage_instance = ProcessStage.from_json(json)
# print the JSON string representation of the object
print(ProcessStage.to_json())

# convert the object into a dict
process_stage_dict = process_stage_instance.to_dict()
# create an instance of ProcessStage from a dict
process_stage_from_dict = ProcessStage.from_dict(process_stage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


