# BrowserImplementation


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | [optional] 
**var_date** | **date** | The date on which the feature was implemented in a browser. (RFC 3339, section 5.6, for example, 2017-07-21) | [optional] 
**version** | **str** | The browser version in which the feature became available. | [optional] 

## Example

```python
from webstatus_openapi.models.browser_implementation import BrowserImplementation

# TODO update the JSON string below
json = "{}"
# create an instance of BrowserImplementation from a JSON string
browser_implementation_instance = BrowserImplementation.from_json(json)
# print the JSON string representation of the object
print(BrowserImplementation.to_json())

# convert the object into a dict
browser_implementation_dict = browser_implementation_instance.to_dict()
# create an instance of BrowserImplementation from a dict
browser_implementation_from_dict = BrowserImplementation.from_dict(browser_implementation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


