# SpecMentor


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**email** | **str** |  | 
**mentored_features** | [**List[FeatureLink]**](FeatureLink.md) |  | 

## Example

```python
from chromestatus_openapi.models.spec_mentor import SpecMentor

# TODO update the JSON string below
json = "{}"
# create an instance of SpecMentor from a JSON string
spec_mentor_instance = SpecMentor.from_json(json)
# print the JSON string representation of the object
print(SpecMentor.to_json())

# convert the object into a dict
spec_mentor_dict = spec_mentor_instance.to_dict()
# create an instance of SpecMentor from a dict
spec_mentor_from_dict = SpecMentor.from_dict(spec_mentor_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


