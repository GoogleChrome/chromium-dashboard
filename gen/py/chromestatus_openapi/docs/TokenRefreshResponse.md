# TokenRefreshResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**token** | **str** |  | [optional] 
**token_expires_sec** | **int** |  | [optional] 

## Example

```python
from chromestatus_openapi.models.token_refresh_response import TokenRefreshResponse

# TODO update the JSON string below
json = "{}"
# create an instance of TokenRefreshResponse from a JSON string
token_refresh_response_instance = TokenRefreshResponse.from_json(json)
# print the JSON string representation of the object
print(TokenRefreshResponse.to_json())

# convert the object into a dict
token_refresh_response_dict = token_refresh_response_instance.to_dict()
# create an instance of TokenRefreshResponse from a dict
token_refresh_response_from_dict = TokenRefreshResponse.from_dict(token_refresh_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


