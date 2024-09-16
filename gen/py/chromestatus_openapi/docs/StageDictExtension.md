# StageDictExtension


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | 
**created** | **datetime** |  | 
**feature_id** | **int** |  | 
**stage_type** | **int** |  | 
**display_name** | **str** |  | 
**intent_stage** | **int** |  | 
**intent_thread_url** | **str** |  | [optional] 
**announcement_url** | **str** |  | [optional] 
**origin_trial_id** | **str** |  | [optional] 
**experiment_goals** | **str** |  | [optional] 
**experiment_risks** | **str** |  | [optional] 
**extensions** | [**List[StageDict]**](StageDict.md) |  | [optional] 
**origin_trial_feedback_url** | **str** |  | [optional] 
**ot_action_requested** | **bool** |  | 
**ot_activation_date** | **datetime** |  | [optional] 
**ot_approval_buganizer_component** | **int** |  | [optional] 
**ot_approval_buganizer_custom_field_id** | **int** |  | [optional] 
**ot_approval_criteria_url** | **str** |  | [optional] 
**ot_approval_group_email** | **str** |  | [optional] 
**ot_chromium_trial_name** | **str** |  | [optional] 
**ot_description** | **str** |  | [optional] 
**ot_display_name** | **str** |  | [optional] 
**ot_documentation_url** | **str** |  | [optional] 
**ot_emails** | **List[str]** |  | 
**ot_feedback_submission_url** | **str** |  | [optional] 
**ot_has_third_party_support** | **bool** |  | 
**ot_is_critical_trial** | **bool** |  | 
**ot_is_deprecation_trial** | **bool** |  | 
**ot_owner_email** | **str** |  | [optional] 
**ot_require_approvals** | **bool** |  | 
**ot_setup_status** | **int** |  | [optional] 
**ot_webfeature_use_counter** | **str** |  | [optional] 
**ot_request_note** | **str** |  | [optional] 
**ot_stage_id** | **int** |  | [optional] 
**experiment_extension_reason** | **str** |  | [optional] 
**finch_url** | **str** |  | [optional] 
**rollout_details** | **str** |  | [optional] 
**rollout_impact** | **int** |  | [optional] 
**rollout_milestone** | **int** |  | [optional] 
**rollout_platforms** | **List[str]** |  | [optional] 
**enterprise_policies** | **List[str]** |  | [optional] 
**pm_emails** | **List[str]** |  | [optional] 
**tl_emails** | **List[str]** |  | [optional] 
**ux_emails** | **List[str]** |  | [optional] 
**te_emails** | **List[str]** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.stage_dict_extension import StageDictExtension

# TODO update the JSON string below
json = "{}"
# create an instance of StageDictExtension from a JSON string
stage_dict_extension_instance = StageDictExtension.from_json(json)
# print the JSON string representation of the object
print(StageDictExtension.to_json())

# convert the object into a dict
stage_dict_extension_dict = stage_dict_extension_instance.to_dict()
# create an instance of StageDictExtension from a dict
stage_dict_extension_from_dict = StageDictExtension.from_dict(stage_dict_extension_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


