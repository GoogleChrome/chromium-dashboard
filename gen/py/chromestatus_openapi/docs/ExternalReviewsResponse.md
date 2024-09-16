# ExternalReviewsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**reviews** | [**List[OutstandingReview]**](OutstandingReview.md) |  | 
**link_previews** | [**List[LinkPreview]**](LinkPreview.md) |  | 

## Example

```python
from chromestatus_openapi.models.external_reviews_response import ExternalReviewsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ExternalReviewsResponse from a JSON string
external_reviews_response_instance = ExternalReviewsResponse.from_json(json)
# print the JSON string representation of the object
print(ExternalReviewsResponse.to_json())

# convert the object into a dict
external_reviews_response_dict = external_reviews_response_instance.to_dict()
# create an instance of ExternalReviewsResponse from a dict
external_reviews_response_from_dict = ExternalReviewsResponse.from_dict(external_reviews_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


