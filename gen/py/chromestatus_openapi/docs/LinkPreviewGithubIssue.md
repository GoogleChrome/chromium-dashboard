# LinkPreviewGithubIssue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewGithubIssueAllOfInformation**](LinkPreviewGithubIssueAllOfInformation.md) |  | 
**http_error_code** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.link_preview_github_issue import LinkPreviewGithubIssue

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewGithubIssue from a JSON string
link_preview_github_issue_instance = LinkPreviewGithubIssue.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewGithubIssue.to_json())

# convert the object into a dict
link_preview_github_issue_dict = link_preview_github_issue_instance.to_dict()
# create an instance of LinkPreviewGithubIssue from a dict
link_preview_github_issue_from_dict = LinkPreviewGithubIssue.from_dict(link_preview_github_issue_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


