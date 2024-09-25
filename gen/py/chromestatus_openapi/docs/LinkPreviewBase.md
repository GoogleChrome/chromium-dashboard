# LinkPreviewBase


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | **object** |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_base import LinkPreviewBase

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewBase from a JSON string
link_preview_base_instance = LinkPreviewBase.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewBase.to_json())

# convert the object into a dict
link_preview_base_dict = link_preview_base_instance.to_dict()
# create an instance of LinkPreviewBase from a dict
link_preview_base_from_dict = LinkPreviewBase.from_dict(link_preview_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


