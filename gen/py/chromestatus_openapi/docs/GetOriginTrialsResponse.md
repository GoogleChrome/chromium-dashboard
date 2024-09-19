# GetOriginTrialsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**origin_trials** | [**List[OriginTrialsInfo]**](OriginTrialsInfo.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.get_origin_trials_response import GetOriginTrialsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetOriginTrialsResponse from a JSON string
get_origin_trials_response_instance = GetOriginTrialsResponse.from_json(json)
# print the JSON string representation of the object
print(GetOriginTrialsResponse.to_json())

# convert the object into a dict
get_origin_trials_response_dict = get_origin_trials_response_instance.to_dict()
# create an instance of GetOriginTrialsResponse from a dict
get_origin_trials_response_from_dict = GetOriginTrialsResponse.from_dict(get_origin_trials_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


