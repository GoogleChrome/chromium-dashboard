# GetVotesResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**votes** | [**List[Vote]**](Vote.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.get_votes_response import GetVotesResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetVotesResponse from a JSON string
get_votes_response_instance = GetVotesResponse.from_json(json)
# print the JSON string representation of the object
print(GetVotesResponse.to_json())

# convert the object into a dict
get_votes_response_dict = get_votes_response_instance.to_dict()
# create an instance of GetVotesResponse from a dict
get_votes_response_from_dict = GetVotesResponse.from_dict(get_votes_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


