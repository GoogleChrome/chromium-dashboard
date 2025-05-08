# ChromiumDailyStatsPage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PageMetadata**](PageMetadata.md) |  | [optional] 
**data** | [**List[ChromiumUsageStat]**](ChromiumUsageStat.md) |  | 

## Example

```python
from webstatus_openapi.models.chromium_daily_stats_page import ChromiumDailyStatsPage

# TODO update the JSON string below
json = "{}"
# create an instance of ChromiumDailyStatsPage from a JSON string
chromium_daily_stats_page_instance = ChromiumDailyStatsPage.from_json(json)
# print the JSON string representation of the object
print(ChromiumDailyStatsPage.to_json())

# convert the object into a dict
chromium_daily_stats_page_dict = chromium_daily_stats_page_instance.to_dict()
# create an instance of ChromiumDailyStatsPage from a dict
chromium_daily_stats_page_from_dict = ChromiumDailyStatsPage.from_dict(chromium_daily_stats_page_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


