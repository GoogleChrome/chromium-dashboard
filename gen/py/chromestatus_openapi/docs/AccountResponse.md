# AccountResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**is_admin** | **bool** |  | [optional] 
**is_site_editor** | **bool** |  | [optional] 
**email** | **str** |  | [optional] 
**id** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.account_response import AccountResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AccountResponse from a JSON string
account_response_instance = AccountResponse.from_json(json)
# print the JSON string representation of the object
print(AccountResponse.to_json())

# convert the object into a dict
account_response_dict = account_response_instance.to_dict()
# create an instance of AccountResponse from a dict
account_response_from_dict = AccountResponse.from_dict(account_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


