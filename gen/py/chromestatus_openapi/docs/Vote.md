# Vote


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature_id** | **int** |  | 
**gate_id** | **int** |  | 
**gate_type** | **int** |  | [optional] 
**set_by** | **str** |  | 
**set_on** | **str** |  | 
**state** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.vote import Vote

# TODO update the JSON string below
json = "{}"
# create an instance of Vote from a JSON string
vote_instance = Vote.from_json(json)
# print the JSON string representation of the object
print(Vote.to_json())

# convert the object into a dict
vote_dict = vote_instance.to_dict()
# create an instance of Vote from a dict
vote_from_dict = Vote.from_dict(vote_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


