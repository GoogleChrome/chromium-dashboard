# FeatureSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_count** | **int** |  | [optional] 
**features** | [**List[VerboseFeatureDict]**](VerboseFeatureDict.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.feature_search_response import FeatureSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureSearchResponse from a JSON string
feature_search_response_instance = FeatureSearchResponse.from_json(json)
# print the JSON string representation of the object
print(FeatureSearchResponse.to_json())

# convert the object into a dict
feature_search_response_dict = feature_search_response_instance.to_dict()
# create an instance of FeatureSearchResponse from a dict
feature_search_response_from_dict = FeatureSearchResponse.from_dict(feature_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


