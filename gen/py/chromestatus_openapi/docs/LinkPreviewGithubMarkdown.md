# LinkPreviewGithubMarkdown


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewGithubMarkdownAllOfInformation**](LinkPreviewGithubMarkdownAllOfInformation.md) |  | 
**http_error_code** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.link_preview_github_markdown import LinkPreviewGithubMarkdown

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewGithubMarkdown from a JSON string
link_preview_github_markdown_instance = LinkPreviewGithubMarkdown.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewGithubMarkdown.to_json())

# convert the object into a dict
link_preview_github_markdown_dict = link_preview_github_markdown_instance.to_dict()
# create an instance of LinkPreviewGithubMarkdown from a dict
link_preview_github_markdown_from_dict = LinkPreviewGithubMarkdown.from_dict(link_preview_github_markdown_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


