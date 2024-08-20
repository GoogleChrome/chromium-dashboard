# LinkPreviewGithubIssueAllOfInformation


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | [optional] 
**number** | **int** |  | [optional] 
**title** | **str** |  | [optional] 
**user_login** | **str** |  | [optional] 
**state** | **str** |  | [optional] 
**state_reason** | **str** |  | [optional] 
**assignee_login** | **str** |  | [optional] 
**created_at** | **date** |  | [optional] 
**updated_at** | **date** |  | [optional] 
**closed_at** | **date** |  | [optional] 
**labels** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_github_issue_all_of_information import LinkPreviewGithubIssueAllOfInformation

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewGithubIssueAllOfInformation from a JSON string
link_preview_github_issue_all_of_information_instance = LinkPreviewGithubIssueAllOfInformation.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewGithubIssueAllOfInformation.to_json())

# convert the object into a dict
link_preview_github_issue_all_of_information_dict = link_preview_github_issue_all_of_information_instance.to_dict()
# create an instance of LinkPreviewGithubIssueAllOfInformation from a dict
link_preview_github_issue_all_of_information_from_dict = LinkPreviewGithubIssueAllOfInformation.from_dict(link_preview_github_issue_all_of_information_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


