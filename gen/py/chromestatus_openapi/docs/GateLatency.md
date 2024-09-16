# GateLatency


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**gate_type** | **int** |  | 
**latency_days** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.gate_latency import GateLatency

# TODO update the JSON string below
json = "{}"
# create an instance of GateLatency from a JSON string
gate_latency_instance = GateLatency.from_json(json)
# print the JSON string representation of the object
print(GateLatency.to_json())

# convert the object into a dict
gate_latency_dict = gate_latency_instance.to_dict()
# create an instance of GateLatency from a dict
gate_latency_from_dict = GateLatency.from_dict(gate_latency_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


