# CreateOriginTrialRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**announcement_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**browser** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_description** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**display_name** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**enterprise_policies** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**finch_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**experiment_goals** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**experiment_risks** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**experiment_extension_reason** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**intent_thread_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**origin_trial_feedback_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**origin_trial_id** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_approval_buganizer_component** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_approval_buganizer_custom_field_id** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_approval_criteria_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_approval_group_email** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_chromium_trial_name** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_display_name** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_action_requested** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_documentation_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_emails** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_feedback_submission_url** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_has_third_party_support** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_is_critical_trial** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_is_deprecation_trial** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_owner_email** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_request_note** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_require_approvals** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_stage_id** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ot_webfeature_use_counter** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**rollout_impact** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**rollout_milestone** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**rollout_platforms** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**rollout_details** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**desktop_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**desktop_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**android_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**android_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ios_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**ios_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**webview_first** | [**FieldInfo**](FieldInfo.md) |  | [optional] 
**webview_last** | [**FieldInfo**](FieldInfo.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.create_origin_trial_request import CreateOriginTrialRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateOriginTrialRequest from a JSON string
create_origin_trial_request_instance = CreateOriginTrialRequest.from_json(json)
# print the JSON string representation of the object
print(CreateOriginTrialRequest.to_json())

# convert the object into a dict
create_origin_trial_request_dict = create_origin_trial_request_instance.to_dict()
# create an instance of CreateOriginTrialRequest from a dict
create_origin_trial_request_from_dict = CreateOriginTrialRequest.from_dict(create_origin_trial_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


