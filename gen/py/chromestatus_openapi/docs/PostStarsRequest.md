# PostStarsRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature_id** | **int** |  | [optional] 
**starred** | **bool** |  | [optional] [default to True]

## Example

```python
from chromestatus_openapi.models.post_stars_request import PostStarsRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostStarsRequest from a JSON string
post_stars_request_instance = PostStarsRequest.from_json(json)
# print the JSON string representation of the object
print(PostStarsRequest.to_json())

# convert the object into a dict
post_stars_request_dict = post_stars_request_instance.to_dict()
# create an instance of PostStarsRequest from a dict
post_stars_request_from_dict = PostStarsRequest.from_dict(post_stars_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


