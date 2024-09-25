# GateInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**gate_type** | **int** |  | [optional] 
**rule** | **str** |  | [optional] 
**approvers** | **str** | A list of approvers. A single string can also be accepted and will be treated as a list containing that string. | [optional] 
**team_name** | **str** |  | [optional] 
**escalation_email** | **str** |  | [optional] 
**slo_initial_response** | **int** | DEFAULT_SLO_LIMIT is 5 in approval_defs.py | [optional] [default to 5]

## Example

```python
from chromestatus_openapi.models.gate_info import GateInfo

# TODO update the JSON string below
json = "{}"
# create an instance of GateInfo from a JSON string
gate_info_instance = GateInfo.from_json(json)
# print the JSON string representation of the object
print(GateInfo.to_json())

# convert the object into a dict
gate_info_dict = gate_info_instance.to_dict()
# create an instance of GateInfo from a dict
gate_info_from_dict = GateInfo.from_dict(gate_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


