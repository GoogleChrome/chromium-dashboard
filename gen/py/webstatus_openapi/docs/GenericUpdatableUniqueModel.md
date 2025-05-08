# GenericUpdatableUniqueModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**updated_at** | **datetime** |  | [optional] 
**created_at** | **datetime** |  | 

## Example

```python
from webstatus_openapi.models.generic_updatable_unique_model import GenericUpdatableUniqueModel

# TODO update the JSON string below
json = "{}"
# create an instance of GenericUpdatableUniqueModel from a JSON string
generic_updatable_unique_model_instance = GenericUpdatableUniqueModel.from_json(json)
# print the JSON string representation of the object
print(GenericUpdatableUniqueModel.to_json())

# convert the object into a dict
generic_updatable_unique_model_dict = generic_updatable_unique_model_instance.to_dict()
# create an instance of GenericUpdatableUniqueModel from a dict
generic_updatable_unique_model_from_dict = GenericUpdatableUniqueModel.from_dict(generic_updatable_unique_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


