# SavedSearchPage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PageMetadata**](PageMetadata.md) |  | [optional] 
**data** | [**List[SavedSearchResponse]**](SavedSearchResponse.md) |  | [optional] 

## Example

```python
from webstatus_openapi.models.saved_search_page import SavedSearchPage

# TODO update the JSON string below
json = "{}"
# create an instance of SavedSearchPage from a JSON string
saved_search_page_instance = SavedSearchPage.from_json(json)
# print the JSON string representation of the object
print(SavedSearchPage.to_json())

# convert the object into a dict
saved_search_page_dict = saved_search_page_instance.to_dict()
# create an instance of SavedSearchPage from a dict
saved_search_page_from_dict = SavedSearchPage.from_dict(saved_search_page_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


