# CommentsRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**comment** | **str** |  | [optional] 
**post_to_thread_type** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.comments_request import CommentsRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CommentsRequest from a JSON string
comments_request_instance = CommentsRequest.from_json(json)
# print the JSON string representation of the object
print(CommentsRequest.to_json())

# convert the object into a dict
comments_request_dict = comments_request_instance.to_dict()
# create an instance of CommentsRequest from a dict
comments_request_from_dict = CommentsRequest.from_dict(comments_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


