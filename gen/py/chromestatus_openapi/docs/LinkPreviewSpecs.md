# LinkPreviewSpecs


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewOpenGraphAllOfInformation**](LinkPreviewOpenGraphAllOfInformation.md) |  | 
**http_error_code** | **int** |  | 

## Example

```python
from chromestatus_openapi.models.link_preview_specs import LinkPreviewSpecs

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewSpecs from a JSON string
link_preview_specs_instance = LinkPreviewSpecs.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewSpecs.to_json())

# convert the object into a dict
link_preview_specs_dict = link_preview_specs_instance.to_dict()
# create an instance of LinkPreviewSpecs from a dict
link_preview_specs_from_dict = LinkPreviewSpecs.from_dict(link_preview_specs_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


