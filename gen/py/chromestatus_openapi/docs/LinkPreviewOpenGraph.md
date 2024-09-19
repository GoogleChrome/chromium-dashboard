# LinkPreviewOpenGraph


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**type** | **str** |  | 
**information** | [**LinkPreviewOpenGraphAllOfInformation**](LinkPreviewOpenGraphAllOfInformation.md) |  | [optional] 
**http_error_code** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.link_preview_open_graph import LinkPreviewOpenGraph

# TODO update the JSON string below
json = "{}"
# create an instance of LinkPreviewOpenGraph from a JSON string
link_preview_open_graph_instance = LinkPreviewOpenGraph.from_json(json)
# print the JSON string representation of the object
print(LinkPreviewOpenGraph.to_json())

# convert the object into a dict
link_preview_open_graph_dict = link_preview_open_graph_instance.to_dict()
# create an instance of LinkPreviewOpenGraph from a dict
link_preview_open_graph_from_dict = LinkPreviewOpenGraph.from_dict(link_preview_open_graph_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


