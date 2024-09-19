# CreateAccountRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**email** | **str** |  | 
**is_admin** | **bool** |  | [optional] 
**is_site_editor** | **bool** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.create_account_request import CreateAccountRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateAccountRequest from a JSON string
create_account_request_instance = CreateAccountRequest.from_json(json)
# print the JSON string representation of the object
print(CreateAccountRequest.to_json())

# convert the object into a dict
create_account_request_dict = create_account_request_instance.to_dict()
# create an instance of CreateAccountRequest from a dict
create_account_request_from_dict = CreateAccountRequest.from_dict(create_account_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


