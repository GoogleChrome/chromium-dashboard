# PostVoteRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | **int** | The vote value to set. 0 for abstain, 1 for approve, 2 for abstain. | 

## Example

```python
from chromestatus_openapi.models.post_vote_request import PostVoteRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostVoteRequest from a JSON string
post_vote_request_instance = PostVoteRequest.from_json(json)
# print the JSON string representation of the object
print(PostVoteRequest.to_json())

# convert the object into a dict
post_vote_request_dict = post_vote_request_instance.to_dict()
# create an instance of PostVoteRequest from a dict
post_vote_request_from_dict = PostVoteRequest.from_dict(post_vote_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


