# CounterEntry


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** |  | [optional] 
**count** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.counter_entry import CounterEntry

# TODO update the JSON string below
json = "{}"
# create an instance of CounterEntry from a JSON string
counter_entry_instance = CounterEntry.from_json(json)
# print the JSON string representation of the object
print(CounterEntry.to_json())

# convert the object into a dict
counter_entry_dict = counter_entry_instance.to_dict()
# create an instance of CounterEntry from a dict
counter_entry_from_dict = CounterEntry.from_dict(counter_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


