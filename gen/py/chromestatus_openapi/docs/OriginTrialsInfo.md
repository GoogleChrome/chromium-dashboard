# OriginTrialsInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**display_name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**origin_trial_feature_name** | **str** |  | [optional] 
**enabled** | **bool** |  | [optional] 
**status** | **str** |  | [optional] 
**chromestatus_url** | **str** |  | [optional] 
**start_milestone** | **str** |  | [optional] 
**end_milestone** | **str** |  | [optional] 
**original_end_milestone** | **str** |  | [optional] 
**end_time** | **str** |  | [optional] 
**documentation_url** | **str** |  | [optional] 
**feedback_url** | **str** |  | [optional] 
**intent_to_experiment_url** | **str** |  | [optional] 
**trial_extensions** | **List[object]** |  | [optional] 
**type** | **str** |  | [optional] 
**allow_third_party_origins** | **bool** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.origin_trials_info import OriginTrialsInfo

# TODO update the JSON string below
json = "{}"
# create an instance of OriginTrialsInfo from a JSON string
origin_trials_info_instance = OriginTrialsInfo.from_json(json)
# print the JSON string representation of the object
print(OriginTrialsInfo.to_json())

# convert the object into a dict
origin_trials_info_dict = origin_trials_info_instance.to_dict()
# create an instance of OriginTrialsInfo from a dict
origin_trials_info_from_dict = OriginTrialsInfo.from_dict(origin_trials_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


