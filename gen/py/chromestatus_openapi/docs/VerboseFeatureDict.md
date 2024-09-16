# VerboseFeatureDict


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | metadata | [optional] 
**created** | [**FeatureDictInnerUserEditInfo**](FeatureDictInnerUserEditInfo.md) |  | [optional] 
**updated** | [**FeatureDictInnerUserEditInfo**](FeatureDictInnerUserEditInfo.md) |  | [optional] 
**accurate_as_of** | **str** |  | [optional] 
**creator_email** | **str** |  | [optional] 
**updater_email** | **str** |  | [optional] 
**owner_emails** | **List[str]** |  | [optional] 
**editor_emails** | **List[str]** |  | [optional] 
**cc_emails** | **List[str]** |  | [optional] 
**spec_mentor_emails** | **List[str]** |  | [optional] 
**unlisted** | **bool** |  | [optional] 
**deleted** | **bool** |  | [optional] 
**editors** | **List[str]** | renamed metadata fields | [optional] 
**cc_recipients** | **List[str]** |  | [optional] 
**spec_mentors** | **List[str]** |  | [optional] 
**creator** | **str** |  | [optional] 
**name** | **str** | descriptive info | [optional] 
**summary** | **str** |  | [optional] 
**category** | **str** |  | [optional] 
**category_int** | **int** |  | [optional] 
**blink_components** | **List[str]** |  | [optional] 
**star_count** | **int** |  | [optional] 
**search_tags** | **List[str]** |  | [optional] 
**feature_notes** | **str** |  | [optional] 
**enterprise_feature_categories** | **List[str]** |  | [optional] 
**feature_type** | **str** | metadata - process info | [optional] 
**feature_type_int** | **int** |  | [optional] 
**intent_stage** | **str** |  | [optional] 
**intent_stage_int** | **int** |  | [optional] 
**active_stage_id** | **int** |  | [optional] 
**bug_url** | **str** |  | [optional] 
**launch_bug_url** | **str** |  | [optional] 
**screenshot_links** | **List[str]** |  | [optional] 
**first_enterprise_notification_milestone** | **int** |  | [optional] 
**breaking_change** | **bool** |  | [optional] 
**enterprise_impact** | **int** |  | [optional] 
**flag_name** | **str** | Implementation in Chrome | [optional] 
**finch_name** | **str** |  | [optional] 
**non_finch_justification** | **str** |  | [optional] 
**ongoing_constraints** | **str** |  | [optional] 
**motivation** | **str** | Topic - Adoption | [optional] 
**devtrial_instructions** | **str** |  | [optional] 
**activation_risks** | **str** |  | [optional] 
**measurement** | **str** |  | [optional] 
**availability_expectation** | **str** |  | [optional] 
**adoption_expectation** | **str** |  | [optional] 
**adoption_plan** | **str** |  | [optional] 
**initial_public_proposal_url** | **str** | Gate | [optional] 
**explainer_links** | **List[str]** |  | [optional] 
**requires_embedder_support** | **bool** |  | [optional] 
**spec_link** | **str** |  | [optional] 
**api_spec** | **str** |  | [optional] 
**prefixed** | **bool** |  | [optional] 
**interop_compat_risks** | **str** |  | [optional] 
**all_platforms** | **bool** |  | [optional] 
**all_platforms_descr** | **bool** |  | [optional] 
**tag_review** | **str** |  | [optional] 
**non_oss_deps** | **str** |  | [optional] 
**anticipated_spec_changes** | **str** |  | [optional] 
**security_risks** | **str** |  | [optional] 
**tags** | **List[str]** |  | [optional] 
**tag_review_status** | **str** |  | [optional] 
**tag_review_status_int** | **int** |  | [optional] 
**security_review_status** | **str** |  | [optional] 
**security_review_status_int** | **int** |  | [optional] 
**privacy_review_status** | **str** |  | [optional] 
**privacy_review_status_int** | **int** |  | [optional] 
**ergonomics_risks** | **str** |  | [optional] 
**wpt** | **bool** |  | [optional] 
**wpt_descr** | **str** |  | [optional] 
**webview_risks** | **str** |  | [optional] 
**devrel_emails** | **List[str]** |  | [optional] 
**debuggability** | **str** |  | [optional] 
**doc_links** | **List[str]** |  | [optional] 
**sample_links** | **List[str]** |  | [optional] 
**stages** | [**List[StageDict]**](StageDict.md) |  | [optional] 
**experiment_timeline** | **str** |  | [optional] 
**resources** | [**FeatureDictInnerResourceInfo**](FeatureDictInnerResourceInfo.md) |  | [optional] 
**comments** | **str** |  | [optional] 
**ff_views** | **int** |  | [optional] 
**safari_views** | **int** |  | [optional] 
**web_dev_views** | **int** |  | [optional] 
**browsers** | [**FeatureBrowsersInfo**](FeatureBrowsersInfo.md) |  | [optional] 
**standards** | [**FeatureDictInnerStandardsInfo**](FeatureDictInnerStandardsInfo.md) |  | [optional] 
**is_released** | **bool** |  | [optional] 
**is_enterprise_feature** | **bool** |  | [optional] 
**updated_display** | **str** |  | [optional] 
**new_crbug_url** | **str** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.verbose_feature_dict import VerboseFeatureDict

# TODO update the JSON string below
json = "{}"
# create an instance of VerboseFeatureDict from a JSON string
verbose_feature_dict_instance = VerboseFeatureDict.from_json(json)
# print the JSON string representation of the object
print(VerboseFeatureDict.to_json())

# convert the object into a dict
verbose_feature_dict_dict = verbose_feature_dict_instance.to_dict()
# create an instance of VerboseFeatureDict from a dict
verbose_feature_dict_from_dict = VerboseFeatureDict.from_dict(verbose_feature_dict_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


