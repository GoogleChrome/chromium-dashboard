# WPTFeatureData


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**score** | **float** |  | [optional] 
**metadata** | **Dict[str, object]** | Contains optional metadata about the metric. This key-value pair is to be considered unstable and can change at any moment. If a field here becomes mature, we can add it to the main WPTFeatureData definition.  | [optional] 

## Example

```python
from webstatus_openapi.models.wpt_feature_data import WPTFeatureData

# TODO update the JSON string below
json = "{}"
# create an instance of WPTFeatureData from a JSON string
wpt_feature_data_instance = WPTFeatureData.from_json(json)
# print the JSON string representation of the object
print(WPTFeatureData.to_json())

# convert the object into a dict
wpt_feature_data_dict = wpt_feature_data_instance.to_dict()
# create an instance of WPTFeatureData from a dict
wpt_feature_data_from_dict = WPTFeatureData.from_dict(wpt_feature_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


