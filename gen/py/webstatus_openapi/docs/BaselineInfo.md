# BaselineInfo

Contains baseline information for a feature.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | [optional] 
**low_date** | **date** |  | [optional] 
**high_date** | **date** |  | [optional] 

## Example

```python
from webstatus_openapi.models.baseline_info import BaselineInfo

# TODO update the JSON string below
json = "{}"
# create an instance of BaselineInfo from a JSON string
baseline_info_instance = BaselineInfo.from_json(json)
# print the JSON string representation of the object
print(BaselineInfo.to_json())

# convert the object into a dict
baseline_info_dict = baseline_info_instance.to_dict()
# create an instance of BaselineInfo from a dict
baseline_info_from_dict = BaselineInfo.from_dict(baseline_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


