# LinkPreviewGithubPullRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewGithubIssueAllOfInformation**](LinkPreviewGithubIssueAllOfInformation.md) |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_github_pull_request import LinkPreviewGithubPullRequest

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewGithubPullRequest from a JSON string
link_preview_github_pull_request_instance = LinkPreviewGithubPullRequest.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewGithubPullRequest.to_json())

# convert the object into a dict
link_preview_github_pull_request_dict = link_preview_github_pull_request_instance.to_dict()
# create an instance of LinkPreviewGithubPullRequest from a dict
link_preview_github_pull_request_from_dict = LinkPreviewGithubPullRequest.from_dict(link_preview_github_pull_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


