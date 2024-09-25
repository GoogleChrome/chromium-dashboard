# LinkPreviewMdnDocs


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewOpenGraphAllOfInformation**](LinkPreviewOpenGraphAllOfInformation.md) |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_mdn_docs import LinkPreviewMdnDocs

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewMdnDocs from a JSON string
link_preview_mdn_docs_instance = LinkPreviewMdnDocs.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewMdnDocs.to_json())

# convert the object into a dict
link_preview_mdn_docs_dict = link_preview_mdn_docs_instance.to_dict()
# create an instance of LinkPreviewMdnDocs from a dict
link_preview_mdn_docs_from_dict = LinkPreviewMdnDocs.from_dict(link_preview_mdn_docs_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


