# SavedSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**updated_at** | **datetime** |  | [optional] 
**created_at** | **datetime** |  | 
**name** | **str** |  | 
**query** | **str** |  | 
**subscription_status** | **str** | The subscription status for a saved search for a user. This field is only populated when the request is authenticated.  | [optional] 
**owner_status** | **str** | The owner status for a saved search for a user. This field is only populated when the request is authenticated.  | [optional] 

## Example

```python
from webstatus_openapi.models.saved_search_response import SavedSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SavedSearchResponse from a JSON string
saved_search_response_instance = SavedSearchResponse.from_json(json)
# print the JSON string representation of the object
print(SavedSearchResponse.to_json())

# convert the object into a dict
saved_search_response_dict = saved_search_response_instance.to_dict()
# create an instance of SavedSearchResponse from a dict
saved_search_response_from_dict = SavedSearchResponse.from_dict(saved_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


