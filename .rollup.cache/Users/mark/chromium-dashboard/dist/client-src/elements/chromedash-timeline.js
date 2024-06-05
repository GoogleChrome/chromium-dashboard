import { __extends, __makeTemplateObject, __spreadArray } from "tslib";
import { LitElement, css, html, nothing } from 'lit';
import { SHARED_STYLES } from '../css/shared-css.js';
import { showToastMessage } from './utils.js';
var ChromedashTimeline = /** @class */ (function (_super) {
    __extends(ChromedashTimeline, _super);
    function ChromedashTimeline() {
        var _this = _super.call(this) || this;
        _this.selectedBucketId = '1';
        _this.showAllHistoricalData = false;
        _this.type = '';
        _this.view = '';
        _this.props = [];
        return _this;
    }
    Object.defineProperty(ChromedashTimeline, "properties", {
        get: function () {
            return {
                type: { type: String },
                view: { type: String },
                props: { attribute: false },
                selectedBucketId: { attribute: false },
                showAllHistoricalData: { attribute: false },
            };
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ChromedashTimeline, "styles", {
        get: function () {
            return __spreadArray(__spreadArray([], SHARED_STYLES, true), [
                css(templateObject_1 || (templateObject_1 = __makeTemplateObject(["\n        :host {\n          display: block;\n          flex: 1;\n          width: var(--max-content-width);\n        }\n\n        :host label {\n          margin-left: 8px;\n          cursor: pointer;\n        }\n\n        #chart {\n          margin-top: 15px;\n          width: 100%;\n          height: 450px;\n          background: var(--table-alternate-background);\n          border-radius: var(--border-radius);\n        }\n\n        #http-archive-data {\n          border: 0;\n          width: 100%;\n          height: 870px;\n        }\n\n        .header_title {\n          margin: 32px 0 15px 0;\n          font-weight: 500;\n          color: #000;\n        }\n\n        .description {\n          margin: 15px 0;\n        }\n\n        .callout {\n          padding: var(--content-padding);\n          margin-top: var(--content-padding);\n          background-color: var(--md-yellow-100);\n          border-color: rgba(27, 31, 35, 0.15);\n          line-height: 1.4;\n        }\n\n        #bigquery:empty {\n          display: none;\n        }\n\n        #bigquery {\n          font-family: 'Courier New', Courier, monospace;\n          font-weight: 600;\n          padding: 15px;\n          margin-bottom: 100px;\n          background: var(--table-alternate-background);\n          display: inline-block;\n        }\n\n        #datalist-input {\n          width: 20em;\n          border-radius: 10px;\n          height: 25px;\n          padding-left: 10px;\n          font-size: 15px;\n        }\n\n        sl-progress-bar {\n          --height: 4px;\n          --track-color: var(--barchart-foreground);\n          --indicator-color: var(--barchart-background);\n        }\n      "], ["\n        :host {\n          display: block;\n          flex: 1;\n          width: var(--max-content-width);\n        }\n\n        :host label {\n          margin-left: 8px;\n          cursor: pointer;\n        }\n\n        #chart {\n          margin-top: 15px;\n          width: 100%;\n          height: 450px;\n          background: var(--table-alternate-background);\n          border-radius: var(--border-radius);\n        }\n\n        #http-archive-data {\n          border: 0;\n          width: 100%;\n          height: 870px;\n        }\n\n        .header_title {\n          margin: 32px 0 15px 0;\n          font-weight: 500;\n          color: #000;\n        }\n\n        .description {\n          margin: 15px 0;\n        }\n\n        .callout {\n          padding: var(--content-padding);\n          margin-top: var(--content-padding);\n          background-color: var(--md-yellow-100);\n          border-color: rgba(27, 31, 35, 0.15);\n          line-height: 1.4;\n        }\n\n        #bigquery:empty {\n          display: none;\n        }\n\n        #bigquery {\n          font-family: 'Courier New', Courier, monospace;\n          font-weight: 600;\n          padding: 15px;\n          margin-bottom: 100px;\n          background: var(--table-alternate-background);\n          display: inline-block;\n        }\n\n        #datalist-input {\n          width: 20em;\n          border-radius: 10px;\n          height: 25px;\n          padding-left: 10px;\n          font-size: 15px;\n        }\n\n        sl-progress-bar {\n          --height: 4px;\n          --track-color: var(--barchart-foreground);\n          --indicator-color: var(--barchart-background);\n        }\n      "]))),
            ], false);
        },
        enumerable: false,
        configurable: true
    });
    ChromedashTimeline.prototype.updated = function () {
        window.google.charts.setOnLoadCallback(this._updateTimeline.bind(this));
    };
    ChromedashTimeline.prototype.updateSelectedBucketId = function (e) {
        var inputValue = e.currentTarget.value;
        var feature = this.props.find(function (el) { return el[1] === inputValue; });
        if (feature) {
            this.selectedBucketId = feature[0].toString();
        }
        else if (inputValue) {
            showToastMessage('No matching features. Please try again!');
        }
    };
    ChromedashTimeline.prototype.toggleShowAllHistoricalData = function () {
        this.showAllHistoricalData = !this.showAllHistoricalData;
    };
    ChromedashTimeline.prototype.firstUpdated = function () {
        window.google.charts.load('current', { packages: ['corechart'] });
    };
    ChromedashTimeline.prototype.drawVisualization = function (data, bucketId, showAllHistoricalData) {
        var datatable = new google.visualization.DataTable();
        datatable.addColumn('date', 'Date');
        datatable.addColumn('number', 'Percentage');
        datatable.addColumn({ type: 'string', role: 'annotation' });
        datatable.addColumn({ type: 'string', role: 'annotationText' });
        var rowArray = [];
        for (var i = 0, item = void 0; (item = data[i]); ++i) {
            var dateStr = item.date.split('-');
            var date = new Date();
            date.setFullYear(parseInt(dateStr[0]), parseInt(dateStr[1]) - 1, parseInt(dateStr[2]));
            var row = [date, parseFloat((item.day_percentage * 100).toFixed(6))];
            // Add annotation where UMA data switched to new stuff.
            if (item.date === '2017-10-27') {
                row.push('A', 'Modernized metrics');
            }
            else {
                row.push(null, null);
            }
            rowArray.push(row);
        }
        datatable.addRows(rowArray);
        function aggregateByMonth(date) {
            var month = date.getMonth();
            var year = date.getFullYear();
            return new Date(year, month);
        }
        var groupedTable = window.google.visualization.data.group(datatable, [{ column: 0, modifier: aggregateByMonth, type: 'date' }], [
            {
                column: 1,
                aggregation: window.google.visualization.data.avg,
                type: 'number',
                label: 'Monthly Average',
            },
        ], [{ column: 2, type: 'string' }]);
        var formatter = new window.google.visualization.NumberFormat({
            fractionDigits: 6,
        });
        formatter.format(groupedTable, 1); // Apply formatter to percentage column.
        var view = groupedTable;
        if (!showAllHistoricalData) {
            var startYear = new Date().getFullYear() - 2; // Show only 2 years of data by default.
            view = new window.google.visualization.DataView(groupedTable);
            view.setRows(view.getFilteredRows([{ column: 0, minValue: new Date(startYear, 0, 1) }]));
        }
        var chartEl = this.shadowRoot.querySelector('#chart');
        var chart = new window.google.visualization.LineChart(chartEl);
        chart.draw(view, {
            backgroundColor: 'white',
            legend: { position: 'none' },
            curveType: 'function',
            vAxis: {
                title: '% page loads',
                // maxValue: 100,
                minValue: 0,
            },
            hAxis: {
                title: 'Date',
                format: 'MMM d, YYYY',
            },
            width: '100%',
            height: '100%',
            pointSize: 4,
            series: { 0: { color: '#4580c0' } },
            trendlines: {
                0: {
                    type: 'linear',
                    opacity: 0.5,
                    color: '#bdd6ed',
                    pointsVisible: false,
                },
            },
        });
    };
    ChromedashTimeline.prototype._updateTimeline = function () {
        var _this = this;
        if (this.selectedBucketId === '1' || !this.props.length)
            return;
        var url = '/data/timeline/' +
            this.type +
            this.view +
            '?bucket_id=' +
            this.selectedBucketId;
        // [DEV] Change to true to use the staging server endpoint for development
        var devMode = false;
        if (devMode)
            url = 'https://cr-status-staging.appspot.com' + url;
        this._renderHTTPArchiveData();
        // the chartEl's innerHTML will get overwritten once the chart is loaded
        var chartEl = this.shadowRoot.querySelector('#chart');
        if (!chartEl.innerHTML.includes('sl-progress-bar')) {
            chartEl.insertAdjacentHTML('afterbegin', '<sl-progress-bar indeterminate></sl-progress-bar>');
        }
        var options = { credentials: 'omit' };
        fetch(url, options)
            .then(function (res) { return res.json(); })
            .then(function (response) {
            _this.drawVisualization(response, _this.selectedBucketId, _this.showAllHistoricalData);
        });
        var currentUrl = '/metrics/' +
            this.type +
            '/timeline/' +
            this.view +
            '/' +
            this.selectedBucketId;
        if (history.pushState && location.pathname != currentUrl) {
            history.pushState({ id: this.selectedBucketId }, '', currentUrl);
        }
    };
    ChromedashTimeline.prototype._renderHTTPArchiveData = function () {
        var _this = this;
        var feature = this.props.find(function (el) { return el[0] === parseInt(_this.selectedBucketId); });
        if (feature) {
            var featureName = feature[1];
            var inputEl = this.shadowRoot.querySelector('#datalist-input');
            inputEl.value = featureName;
            if (this.type == 'css') {
                featureName = convertToCamelCaseFeatureName(featureName);
            }
            var REPORT_ID = '1M8kXOqPkwYNKjJhtag_nvDNJCpvmw_ri';
            var dsEmbedUrl = "https://datastudio.google.com/embed/reporting/".concat(REPORT_ID, "/page/tc5b?params=%7B\"df3\":\"include%25EE%2580%25800%25EE%2580%2580IN%25EE%2580%2580").concat(featureName, "\"%7D");
            var hadEl = this.shadowRoot.querySelector('#http-archive-data');
            hadEl.src = dsEmbedUrl;
            var bigqueryEl = this.shadowRoot.querySelector('#bigquery');
            bigqueryEl.textContent = "#standardSQL\nSELECT yyyymmdd, client, pct_urls, sample_urls\nFROM `httparchive.blink_features.usage`\nWHERE feature = '".concat(featureName, "'\nAND yyyymmdd = (SELECT MAX(yyyymmdd) FROM `httparchive.blink_features.usage`)\nORDER BY yyyymmdd DESC, client");
        }
    };
    ChromedashTimeline.prototype.render = function () {
        var note2017 = html(templateObject_2 || (templateObject_2 = __makeTemplateObject(["\n      <p class=\"callout\">\n        <b>Note</b>: on 2017-10-26 the underlying metrics were switched over to\n        a newer collection system which is\n        <a\n          href=\"https://groups.google.com/a/chromium.org/forum/#!msg/blink-api-owners-discuss/IpIkbz0qtrM/HUCfSMv2AQAJ\"\n          target=\"_blank\"\n          >more accurate</a\n        >. This is also the reason for the abrupt spike around 2017-10-26.\n      </p>\n    "], ["\n      <p class=\"callout\">\n        <b>Note</b>: on 2017-10-26 the underlying metrics were switched over to\n        a newer collection system which is\n        <a\n          href=\"https://groups.google.com/a/chromium.org/forum/#!msg/blink-api-owners-discuss/IpIkbz0qtrM/HUCfSMv2AQAJ\"\n          target=\"_blank\"\n          >more accurate</a\n        >. This is also the reason for the abrupt spike around 2017-10-26.\n      </p>\n    "])));
        return html(templateObject_4 || (templateObject_4 = __makeTemplateObject(["\n      <input\n        id=\"datalist-input\"\n        type=\"search\"\n        list=\"features\"\n        placeholder=\"Select or search a property\"\n        @change=\"", "\"\n      />\n      <datalist id=\"features\">\n        ", "\n      </datalist>\n      <label>\n        Show all historical data:\n        <input\n          type=\"checkbox\"\n          ?checked=\"", "\"\n          @change=\"", "\"\n        />\n      </label>\n      <h3 id=\"usage\" class=\"header_title\">\n        Percentage of page loads over time\n      </h3>\n      <p class=\"description\">\n        The chart below shows the percentage of page loads (in Chrome) that use\n        this feature at least once. Data is across all channels and platforms.\n        Newly added use counters that are not on Chrome stable yet only have\n        data from the Chrome channels they're on.\n      </p>\n      <div id=\"chart\"></div>\n      ", "\n      <h3 id=\"httparchive\" class=\"header_title\">\n        Adoption of the feature on top sites\n      </h3>\n      <p class=\"description\">\n        The chart below shows the adoption of the feature by the top URLs on the\n        internet. Data from\n        <a href=\"https://httparchive.org/\" target=\"_blank\">HTTP Archive</a>.\n      </p>\n      <iframe id=\"http-archive-data\"></iframe>\n      <p class=\"callout\">\n        <b>Note</b>: The jump around July and December 2018 are because the\n        corpus of URLs crawled by HTTP Archive increased. These jumps have no\n        correlation with the jump in the top graph. See the\n        <a\n          href=\"https://discuss.httparchive.org/t/changes-to-the-http-archive-corpus/1539\"\n          target=\"_blank\"\n          >announcement</a\n        >\n        for more details.\n      </p>\n      <p class=\"description\">\n        Copy and run this command in\n        <a href=\"https://bigquery.cloud.google.com\" target=\"_blank\">BigQuery</a>\n        to produce similar results:\n      </p>\n      <pre id=\"bigquery\"></pre>\n    "], ["\n      <input\n        id=\"datalist-input\"\n        type=\"search\"\n        list=\"features\"\n        placeholder=\"Select or search a property\"\n        @change=\"", "\"\n      />\n      <datalist id=\"features\">\n        ", "\n      </datalist>\n      <label>\n        Show all historical data:\n        <input\n          type=\"checkbox\"\n          ?checked=\"", "\"\n          @change=\"", "\"\n        />\n      </label>\n      <h3 id=\"usage\" class=\"header_title\">\n        Percentage of page loads over time\n      </h3>\n      <p class=\"description\">\n        The chart below shows the percentage of page loads (in Chrome) that use\n        this feature at least once. Data is across all channels and platforms.\n        Newly added use counters that are not on Chrome stable yet only have\n        data from the Chrome channels they're on.\n      </p>\n      <div id=\"chart\"></div>\n      ", "\n      <h3 id=\"httparchive\" class=\"header_title\">\n        Adoption of the feature on top sites\n      </h3>\n      <p class=\"description\">\n        The chart below shows the adoption of the feature by the top URLs on the\n        internet. Data from\n        <a href=\"https://httparchive.org/\" target=\"_blank\">HTTP Archive</a>.\n      </p>\n      <iframe id=\"http-archive-data\"></iframe>\n      <p class=\"callout\">\n        <b>Note</b>: The jump around July and December 2018 are because the\n        corpus of URLs crawled by HTTP Archive increased. These jumps have no\n        correlation with the jump in the top graph. See the\n        <a\n          href=\"https://discuss.httparchive.org/t/changes-to-the-http-archive-corpus/1539\"\n          target=\"_blank\"\n          >announcement</a\n        >\n        for more details.\n      </p>\n      <p class=\"description\">\n        Copy and run this command in\n        <a href=\"https://bigquery.cloud.google.com\" target=\"_blank\">BigQuery</a>\n        to produce similar results:\n      </p>\n      <pre id=\"bigquery\"></pre>\n    "])), this.updateSelectedBucketId, this.props.map(function (prop) { return html(templateObject_3 || (templateObject_3 = __makeTemplateObject(["\n            <option\n              value=\"", "\"\n              dataset-debug-bucket-id=\"", "\"\n            ></option>\n          "], ["\n            <option\n              value=\"", "\"\n              dataset-debug-bucket-id=\"", "\"\n            ></option>\n          "])), prop[1], prop[0]); }), this.showAllHistoricalData, this.toggleShowAllHistoricalData, this.showAllHistoricalData ? note2017 : nothing);
    };
    return ChromedashTimeline;
}(LitElement));
// Capitalizes the first letter of a word.
function capitalize(word) {
    var letters = word.split('');
    letters[0] = letters[0].toUpperCase();
    return letters.join('');
}
// Converts 'background-image' to 'CSSPropertyBackgroundImage'.
function convertToCamelCaseFeatureName(property) {
    return 'CSSProperty' + property.split('-').map(capitalize).join('');
}
customElements.define('chromedash-timeline', ChromedashTimeline);
var templateObject_1, templateObject_2, templateObject_3, templateObject_4;
//# sourceMappingURL=chromedash-timeline.js.map