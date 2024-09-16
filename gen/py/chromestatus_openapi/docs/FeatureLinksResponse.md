# FeatureLinksResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[LinkPreviewBase]**](LinkPreviewBase.md) |  | [optional] 
**has_stale_links** | **bool** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_links_response import FeatureLinksResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureLinksResponse from a JSON string
feature_links_response_instance = FeatureLinksResponse.from_json(json)
# print the JSON string representation of the object
print(FeatureLinksResponse.to_json())

# convert the object into a dict
feature_links_response_dict = feature_links_response_instance.to_dict()
# create an instance of FeatureLinksResponse from a dict
feature_links_response_from_dict = FeatureLinksResponse.from_dict(feature_links_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


