# Gate


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | [optional] 
**feature_id** | **int** |  | [optional] 
**stage_id** | **int** |  | [optional] 
**gate_type** | **int** |  | [optional] 
**team_name** | **str** |  | [optional] 
**gate_name** | **str** |  | [optional] 
**escalation_email** | **str** |  | [optional] 
**state** | **int** |  | [optional] 
**requested_on** | **datetime** |  | [optional] 
**responded_on** | **datetime** |  | [optional] 
**assignee_emails** | **List[str]** |  | [optional] 
**next_action** | **str** |  | [optional] 
**additional_review** | **bool** |  | [optional] 
**slo_initial_response** | **int** | DEFAULT_SLO_LIMIT is 5 in approval_defs.py | [optional] [default to 5]
**slo_initial_response_took** | **int** |  | [optional] 
**slo_initial_response_remaining** | **int** |  | [optional] 
**possible_assignee_emails** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.gate import Gate

# TODO update the JSON string below
json = "{}"
# create an instance of Gate from a JSON string
gate_instance = Gate.from_json(json)
# print the JSON string representation of the object
print(Gate.to_json())

# convert the object into a dict
gate_dict = gate_instance.to_dict()
# create an instance of Gate from a dict
gate_from_dict = Gate.from_dict(gate_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


