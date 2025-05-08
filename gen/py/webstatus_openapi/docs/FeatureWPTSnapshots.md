# FeatureWPTSnapshots


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**stable** | [**Dict[str, WPTFeatureData]**](WPTFeatureData.md) | Contains snapshot of the stable WPT data. The keys for the object comes from the different cases in https://github.com/web-platform-tests/wpt.fyi/blob/fb5bae7c6d04563864ef1c28a263a0a8d6637c4e/shared/product_spec.go#L71-L104  | [optional] 
**experimental** | [**Dict[str, WPTFeatureData]**](WPTFeatureData.md) | Contains snapshot of the experimental WPT data. The keys for the object comes from the different cases in https://github.com/web-platform-tests/wpt.fyi/blob/fb5bae7c6d04563864ef1c28a263a0a8d6637c4e/shared/product_spec.go#L71-L104  | [optional] 

## Example

```python
from webstatus_openapi.models.feature_wpt_snapshots import FeatureWPTSnapshots

# TODO update the JSON string below
json = "{}"
# create an instance of FeatureWPTSnapshots from a JSON string
feature_wpt_snapshots_instance = FeatureWPTSnapshots.from_json(json)
# print the JSON string representation of the object
print(FeatureWPTSnapshots.to_json())

# convert the object into a dict
feature_wpt_snapshots_dict = feature_wpt_snapshots_instance.to_dict()
# create an instance of FeatureWPTSnapshots from a dict
feature_wpt_snapshots_from_dict = FeatureWPTSnapshots.from_dict(feature_wpt_snapshots_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


