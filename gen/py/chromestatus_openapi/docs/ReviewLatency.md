# ReviewLatency


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**feature** | [**FeatureLink**](FeatureLink.md) |  | 
**gate_reviews** | [**List[GateLatency]**](GateLatency.md) |  | 

## Example

```python
from chromestatus_openapi.models.review_latency import ReviewLatency

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewLatency from a JSON string
review_latency_instance = ReviewLatency.from_json(json)
# print the JSON string representation of the object
print(ReviewLatency.to_json())

# convert the object into a dict
review_latency_dict = review_latency_instance.to_dict()
# create an instance of ReviewLatency from a dict
review_latency_from_dict = ReviewLatency.from_dict(review_latency_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


