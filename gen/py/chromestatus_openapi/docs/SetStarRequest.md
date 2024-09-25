# SetStarRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature_id** | **int** |  | [optional] 
**starred** | **bool** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.set_star_request import SetStarRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SetStarRequest from a JSON string
set_star_request_instance = SetStarRequest.from_json(json)
# print the JSON string representation of the object
print(SetStarRequest.to_json())

# convert the object into a dict
set_star_request_dict = set_star_request_instance.to_dict()
# create an instance of SetStarRequest from a dict
set_star_request_from_dict = SetStarRequest.from_dict(set_star_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


