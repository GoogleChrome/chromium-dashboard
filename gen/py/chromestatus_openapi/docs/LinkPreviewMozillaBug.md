# LinkPreviewMozillaBug


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewOpenGraphAllOfInformation**](LinkPreviewOpenGraphAllOfInformation.md) |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_mozilla_bug import LinkPreviewMozillaBug

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewMozillaBug from a JSON string
link_preview_mozilla_bug_instance = LinkPreviewMozillaBug.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewMozillaBug.to_json())

# convert the object into a dict
link_preview_mozilla_bug_dict = link_preview_mozilla_bug_instance.to_dict()
# create an instance of LinkPreviewMozillaBug from a dict
link_preview_mozilla_bug_from_dict = LinkPreviewMozillaBug.from_dict(link_preview_mozilla_bug_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


