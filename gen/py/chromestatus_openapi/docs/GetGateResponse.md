# GetGateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**gates** | [**List[Gate]**](Gate.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.get_gate_response import GetGateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetGateResponse from a JSON string
get_gate_response_instance = GetGateResponse.from_json(json)
# print the JSON string representation of the object
print(GetGateResponse.to_json())

# convert the object into a dict
get_gate_response_dict = get_gate_response_instance.to_dict()
# create an instance of GetGateResponse from a dict
get_gate_response_from_dict = GetGateResponse.from_dict(get_gate_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


