# LinkPreview


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | **object** |  | 
**http_error_code** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.link_preview import LinkPreview

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreview from a JSON string
link_preview_instance = LinkPreview.from_json(json)
# print the JSON string representation of the object
print(LinkPreview.to_json())

# convert the object into a dict
link_preview_dict = link_preview_instance.to_dict()
# create an instance of LinkPreview from a dict
link_preview_from_dict = LinkPreview.from_dict(link_preview_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


