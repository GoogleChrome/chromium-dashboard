# Activity


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**comment_id** | **int** |  | 
**feature_id** | **int** |  | 
**gate_id** | **int** |  | [optional] 
**created** | **str** |  | 
**author** | **str** |  | 
**content** | **str** |  | 
**deleted_by** | **str** |  | [optional] 
**amendments** | [**List[Amendment]**](Amendment.md) |  | [optional] 

## Example

```python
from chromestatus_openapi.models.activity import Activity

# TODO update the JSON string below
json = "{}"
# create an instance of Activity from a JSON string
activity_instance = Activity.from_json(json)
# print the JSON string representation of the object
print(Activity.to_json())

# convert the object into a dict
activity_dict = activity_instance.to_dict()
# create an instance of Activity from a dict
activity_from_dict = Activity.from_dict(activity_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


