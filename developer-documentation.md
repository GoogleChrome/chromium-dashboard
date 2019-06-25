# chromedash developer documentation

This doc covers some basic overview of the codebase to help developers navigate.

In summary, this web app is using Django as the backend and lit-element in the front end.

## Front end

Front end codes exist in two parts: main site (including admin) and http2push.

### Main site page renderring

All the pages are rendered in a combination of Django template (`/templates`) and front-end components (`/static/elements`).

1. `/templates/base.html` and `/templates/base_embed.html` are the html skeleton.
1. Templates in `/templates` (extend the `base.html` or `embed_base.html`) are the Django templates for each page.
    - lit-element components, css, js files are all imported/included in those templates.
    - We pass backend variables to js like this: `const variableInJs = {{variable_in_template|safe}}`.
1. All lit-element components are in `/static/elements`.
1. All JavaScript files are in `/static/js-src/` and processed by gulp, then output to '/static/js/' and get included in templates.
1. All CSS files are in `/static/sass/` and processed by gulp, then output to `/static/css/` and get included in templates.
1. A service worker is created by gulp too. Output in `/static/dist/service-worker.js`.

## Some nice-to-fix

- Wrap page in a component, so the data flow is more clear. Benefits: no need to assigns component properties from js files; no need to pass element reference to components to get value (e.g. we are passing searchEl to chromedash-featurelist.).
- Some buttons are a / span / div.

## Content from the old developer doc (some are out-of-date)

** index.html
*
* The 'Most Popular' page.
*
* This file is to show 10 charts. They will be charts from
* the top 10 Properties of the stack rank page.
*
* This implementation is not complete.
* This depends upon stack rank.
*
**

** stackrank.html
*
* Lists all properties from highest popularity to least
* User may reverse order
*
* Will function, once a date is specified in QueryStackRank of main.py
*
**

** main.py
*
* Handler File
*
* /data/querystableinstances performs a query to get all instances
* from the database. This data is converted to JSON and written to
* the page.
*
* /data/querystackrank performs a query to get most recent day's
* popularity rank in default descending order. The data is converted to
* JSON and written to the page.
*
**

** admin.py
*
* Handler File
*
* visiting /cron/metrics calls YesterdayHandler which retrieves yesterday's data from the UMA Cloud Storage.
* This is how the cron job is updating - Daily grabbing the previous day's data
* The data is parsed and stored as:
* class StableInstance(DictModel):
*     property_name = db.StringProperty();
*     bucket_id = db.IntegerProperty();
*     date = db.DateProperty();
*     day_percentage = db.FloatProperty();
*     rolling_percentage = db.FloatProperty();
*
* visiting /cron/histograms calls HistogramsHandler which retrieves FeatureObserver and
* FeatureObserver histograms from chromium.googlesource.com.
* 
* ACTION REQUIRED: we will need to replace histogramID with the appropriate ID.
* This can be obtained from uma.googleplex.com/data/histograms/ids-chrome-histograms.txt
* Searching this file for CSS Properties, once our histogram has data should give us a hex
* value which should be converted to an integer.
*
* 


** featurelevel.js
*
* Creates charts for the feature level page.
* 
* drawVisualization()
* This function takes in the name of the property for which the graph is being drawn.
* (This should probably be changed to the propertyID/bucketID in the future.)
* We iterate through parsed data, building up a data object which we can pass to chart.draw()
* The desired form of data to pass to chart.draw() is:
*  [[Date,    Name,      Percentage]
*   [Mar 3,   Color,     60]
*   [Mar 4,   Width,     70]]
*  ** If we need to look into further optimization, building this data structure is probably the place it can happen.
*
* getNamesArray()
* Takes the desired name to have displayed on the chart. Checks if there is a correspinding property (prefixed or unprefixed)
* adds the given name plus the corresponding name to an array and returns the array.
*
** 



appcfg.py upload_data --config_file=bulkloader.yaml --kind=Feature --url=https://chromestatus.googleplex.com/_ah/remote_api --filename=import.csv



---

OPTIMIZATIONS
- show/hide less of panel when user clicks it
- recalc style issue perf in chrome 28 (https://src.chromium.org/viewvc/blink?revision=150018&view=revision)
  -> turn on shadow dom polyfill for stable (e.g. Platform = {flags: {shadow: 'polyfill'}};)
- insertBefore issue being fixed: https://code.google.com/p/chromium/issues/detail?id=255734.
  -> Remove inline <style> in elements. 
- Calculate a property in a *Changed handler rather than getters. Latter sets
  up timers if o.Observe() is not present. Former is only calculated once when
  the prop changes.

load features from server. could have also done ajax

elements talk to each other through events and passing chromemetadata in

color-status does its thing. repurposed in mulitple places

chrome-metadata that does auto ajax

render list of features on a filtered view, not entire list.

ajax-delete link element is pretty coo

sass workflow

added tabindex=0  to features so they can be a11yn

dont publish opened in chromedash-feature. Property reflection to attributes
redistribute entire thing in SD polyfill. https://github.com/Polymer/polymer/issues/236

Way sass was written, selectors match from right to left. So *:hover matched
all elements in SD, then filtered on :hover. Change was to be more specific and add tag:

.views {
    @include display-flex;
    @include flex-wrap(wrap);
    
    & > span { // was & > * {
      @include display-flex;
      @include align-items(center);
      position: relative;
      ...
    }
}



the css in ericbidelman's app is the issue
lots of very complex selectors
ex. chromedash-feature section .views > :hover::before
we match from right to left, which means that can "match" <html>
or any descendants
so now hovering anything on that page recalcs style the entire document
same thing with tapping tapping
chromedash-feature section .views > :active::before

the rest of the slow recalcs are [data-first-of-milestone]:first-of-type { ... } in the css for <chromedash-featurelist>
tapping to expand a single row triggers the "invalidate style on all my siblings because of complex selectors" case in Element::recalcStyle

Solution was to remove one selector.

&:first-of-type {
  margin-top: $milestone-label-size + 2;
}
