# PageMetadataWithTotal


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_page_token** | **str** |  | [optional] 
**total** | **int** |  | 

## Example

```python
from webstatus_openapi.models.page_metadata_with_total import PageMetadataWithTotal

# TODO update the JSON string below
json = "{}"
# create an instance of PageMetadataWithTotal from a JSON string
page_metadata_with_total_instance = PageMetadataWithTotal.from_json(json)
# print the JSON string representation of the object
print(PageMetadataWithTotal.to_json())

# convert the object into a dict
page_metadata_with_total_dict = page_metadata_with_total_instance.to_dict()
# create an instance of PageMetadataWithTotal from a dict
page_metadata_with_total_from_dict = PageMetadataWithTotal.from_dict(page_metadata_with_total_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


