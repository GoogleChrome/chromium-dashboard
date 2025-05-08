# FeaturePage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PageMetadataWithTotal**](PageMetadataWithTotal.md) |  | 
**data** | [**List[Feature]**](Feature.md) |  | 

## Example

```python
from webstatus_openapi.models.feature_page import FeaturePage

# TODO update the JSON string below
json = "{}"
# create an instance of FeaturePage from a JSON string
feature_page_instance = FeaturePage.from_json(json)
# print the JSON string representation of the object
print(FeaturePage.to_json())

# convert the object into a dict
feature_page_dict = feature_page_instance.to_dict()
# create an instance of FeaturePage from a dict
feature_page_from_dict = FeaturePage.from_dict(feature_page_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


