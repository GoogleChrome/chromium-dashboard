# BasicErrorModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** |  | 
**code** | **int** |  | 

## Example

```python
from webstatus_openapi.models.basic_error_model import BasicErrorModel

# TODO update the JSON string below
json = "{}"
# create an instance of BasicErrorModel from a JSON string
basic_error_model_instance = BasicErrorModel.from_json(json)
# print the JSON string representation of the object
print(BasicErrorModel.to_json())

# convert the object into a dict
basic_error_model_dict = basic_error_model_instance.to_dict()
# create an instance of BasicErrorModel from a dict
basic_error_model_from_dict = BasicErrorModel.from_dict(basic_error_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


