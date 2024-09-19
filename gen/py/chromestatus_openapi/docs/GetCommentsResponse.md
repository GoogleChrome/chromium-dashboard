# GetCommentsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**comments** | [**List[Activity]**](Activity.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.get_comments_response import GetCommentsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetCommentsResponse from a JSON string
get_comments_response_instance = GetCommentsResponse.from_json(json)
# print the JSON string representation of the object
print(GetCommentsResponse.to_json())

# convert the object into a dict
get_comments_response_dict = get_comments_response_instance.to_dict()
# create an instance of GetCommentsResponse from a dict
get_comments_response_from_dict = GetCommentsResponse.from_dict(get_comments_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


