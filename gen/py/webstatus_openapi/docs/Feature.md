# Feature


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature_id** | **str** |  | 
**name** | **str** | Short name that is intended to be human friendly. Comes from FeatureData&#39;s &#39;name&#39; field in https://github.com/web-platform-dx/web-features/blob/main/schemas/defs.schema.json  | 
**spec** | [**FeatureSpecInfo**](FeatureSpecInfo.md) |  | [optional] 
**browser_implementations** | [**Dict[str, BrowserImplementation]**](BrowserImplementation.md) | Describes the implementation status of the feature. The keys for the object come from https://github.com/web-platform-dx/web-features/blob/8ab08d00b9bdb505af37c435204eb6fe819dfaab/schemas/defs.schema.json#L102-L122  | [optional] 
**baseline** | [**BaselineInfo**](BaselineInfo.md) |  | [optional] 
**usage** | [**BrowserUsage**](BrowserUsage.md) |  | [optional] 
**wpt** | [**FeatureWPTSnapshots**](FeatureWPTSnapshots.md) |  | [optional] 

## Example

```python
from webstatus_openapi.models.feature import Feature

# TODO update the JSON string below
json = "{}"
# create an instance of Feature from a JSON string
feature_instance = Feature.from_json(json)
# print the JSON string representation of the object
print(Feature.to_json())

# convert the object into a dict
feature_dict = feature_instance.to_dict()
# create an instance of Feature from a dict
feature_from_dict = Feature.from_dict(feature_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


