# PatchCommentRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**comment_id** | **int** | The ID of the comment to be updated | 
**is_undelete** | **bool** | Indicates whether to undelete (true) or delete (false) the comment | 

## Example

```python
from chromestatus_openapi.models.patch_comment_request import PatchCommentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchCommentRequest from a JSON string
patch_comment_request_instance = PatchCommentRequest.from_json(json)
# print the JSON string representation of the object
print(PatchCommentRequest.to_json())

# convert the object into a dict
patch_comment_request_dict = patch_comment_request_instance.to_dict()
# create an instance of PatchCommentRequest from a dict
patch_comment_request_from_dict = PatchCommentRequest.from_dict(patch_comment_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


