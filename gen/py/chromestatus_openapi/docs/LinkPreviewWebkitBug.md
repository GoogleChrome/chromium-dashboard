# LinkPreviewWebkitBug


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewOpenGraphAllOfInformation**](LinkPreviewOpenGraphAllOfInformation.md) |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_webkit_bug import LinkPreviewWebkitBug

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewWebkitBug from a JSON string
link_preview_webkit_bug_instance = LinkPreviewWebkitBug.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewWebkitBug.to_json())

# convert the object into a dict
link_preview_webkit_bug_dict = link_preview_webkit_bug_instance.to_dict()
# create an instance of LinkPreviewWebkitBug from a dict
link_preview_webkit_bug_from_dict = LinkPreviewWebkitBug.from_dict(link_preview_webkit_bug_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


