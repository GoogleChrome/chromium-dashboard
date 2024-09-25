# OutstandingReview


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**review_link** | **str** |  | 
**feature** | [**FeatureLink**](FeatureLink.md) |  | 
**current_stage** | **str** | The development stage that the feature has reached:   - [&#x60;incubating&#x60;](https://www.chromium.org/blink/launching-features/#start-incubating)   - [&#x60;prototyping&#x60;](https://www.chromium.org/blink/launching-features/#prototyping)   - [&#x60;dev-trial&#x60;](https://www.chromium.org/blink/launching-features/#dev-trials)   - [&#x60;wide-review&#x60;](https://www.chromium.org/blink/launching-features/#widen-review)   - [&#x60;origin-trial&#x60;](https://www.chromium.org/blink/launching-features/#origin-trials)   - [&#x60;shipping&#x60;](https://www.chromium.org/blink/launching-features/#new-feature-prepare-to-ship)   - &#x60;shipped&#x60; - The feature is enabled by default in Chromium.  | 
**estimated_start_milestone** | **int** |  | [optional] 
**estimated_end_milestone** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.outstanding_review import OutstandingReview

# TODO update the JSON string below
json = "{}"
# create an instance of OutstandingReview from a JSON string
outstanding_review_instance = OutstandingReview.from_json(json)
# print the JSON string representation of the object
print(OutstandingReview.to_json())

# convert the object into a dict
outstanding_review_dict = outstanding_review_instance.to_dict()
# create an instance of OutstandingReview from a dict
outstanding_review_from_dict = OutstandingReview.from_dict(outstanding_review_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


