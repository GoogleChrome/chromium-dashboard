import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashTimeline extends LitElement {
  static get properties() {
    return {
      type: {type: String},
      view: {type: String},
      props: {attribute: false},
      selectedBucketId: {attribute: false},
      showAllHistoricalData: {attribute: false},
    };
  }

  constructor() {
    super();
    this.selectedBucketId = '1';
    this.showAllHistoricalData = false;
    this.type = '';
    this.view = '';
    this.props = [];
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: block;
        flex: 1;
        width: var(--max-content-width);
      }

      :host label {
        margin-left: 8px;
        cursor: pointer;
      }

      #chart {
        margin-top: 15px;
        width: 100%;
        height: 450px;
        background: var(--table-alternate-background);
        border-radius: var(--border-radius);
      }

      #http-archive-data {
        border: 0;
        width: 100%;
        height: 775px;
      }

      .header_title {
        margin: 32px 0 15px 0;
        font-weight: 500;
        color: #000;
      }

      .description {
        margin: 15px 0;
      }

      .callout {
        padding: var(--content-padding);
        margin-top: var(--content-padding);
        background-color: var(--md-yellow-100);
        border-color: rgba(27,31,35,0.15);
        line-height: 1.4;
      }

      #bigquery:empty {
        display: none;
      }

      #bigquery {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 600;
        padding: 15px;
        margin-bottom: 100px;
        background: var(--table-alternate-background);
        display: inline-block;
      }

      #datalist-input {
        width: 20em;
        border-radius: 10px;
        height: 25px;
        padding-left: 10px;
        font-size: 15px;
      }

      sl-progress-bar {
        --height: 4px;
        --track-color: var(--barchart-foreground);
        --indicator-color: var(--barchart-background);
      }
    `];
  }

  updated() {
    this._updateTimeline();
  }

  updateSelectedBucketId(e) {
    const inputValue = e.currentTarget.value;
    const feature = this.props.find((el) => el[1] === inputValue);
    if (feature) {
      this.selectedBucketId = feature[0];
    } else if (inputValue) {
      showToastMessage('No matching features. Please try again!');
    }
  }

  toggleShowAllHistoricalData() {
    this.showAllHistoricalData = !this.showAllHistoricalData;
  }

  firstUpdated() {
    window.google.charts.load('current', {'packages': ['corechart']});
  }

  drawVisualization(data, bucketId, showAllHistoricalData) {
    const datatable = new google.visualization.DataTable();
    datatable.addColumn('date', 'Date');
    datatable.addColumn('number', 'Percentage');
    datatable.addColumn({type: 'string', role: 'annotation'});
    datatable.addColumn({type: 'string', role: 'annotationText'});

    const rowArray = [];
    for (let i = 0, item; item = data[i]; ++i) {
      const dateStr = item.date.split('-');
      const date = new Date();
      date.setFullYear(parseInt(dateStr[0]), parseInt(dateStr[1]) - 1, parseInt(dateStr[2]));
      const row = [date, parseFloat((item.day_percentage * 100).toFixed(6))];
      // Add annotation where UMA data switched to new stuff.
      if (item.date === '2017-10-27') {
        row.push('A', 'Modernized metrics');
      } else {
        row.push(null, null);
      }
      rowArray.push(row);
    }

    datatable.addRows(rowArray);

    function aggregateByMonth(date) {
      const month = date.getMonth();
      const year = date.getFullYear();
      return new Date(year, month);
    }

    const groupedTable = window.google.visualization.data.group(datatable,
      [{column: 0, modifier: aggregateByMonth, type: 'date'}],
      [{
        column: 1,
        aggregation: window.google.visualization.data.avg,
        type: 'number',
        label: 'Monthly Average',
      }],
      [{column: 2, type: 'string'}],
    );

    const formatter = new window.google.visualization.NumberFormat({fractionDigits: 6});
    formatter.format(groupedTable, 1); // Apply formatter to percentage column.

    let view = groupedTable;

    if (!showAllHistoricalData) {
      const startYear = (new Date()).getFullYear() - 2; // Show only 2 years of data by default.
      view = new window.google.visualization.DataView(groupedTable);
      view.setRows(view.getFilteredRows([{column: 0, minValue: new Date(startYear, 0, 1)}]));
    }

    const chartEl = this.shadowRoot.querySelector('#chart');
    const chart = new window.google.visualization.LineChart(chartEl);
    chart.draw(view, {
      backgroundColor: 'white',
      legend: {position: 'none'},
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
      series: {0: {color: '#4580c0'}},
      trendlines: {
        0: {
          type: 'linear',
          opacity: 0.5,
          color: '#bdd6ed',
          pointsVisible: false,
        },
      },
    });
  }

  _updateTimeline() {
    if (this.selectedBucketId === '1' || !this.props.length) return;

    let url = '/data/timeline/' + this.type + this.view +
              '?bucket_id=' + this.selectedBucketId;

    // [DEV] Change to true to use the staging server endpoint for development
    const devMode = false;
    if (devMode) url = 'https://cr-status-staging.appspot.com' + url;

    this._renderHTTPArchiveData();

    // the chartEl's innerHTML will get overwritten once the chart is loaded
    const chartEl = this.shadowRoot.querySelector('#chart');
    if (!chartEl.innerHTML.includes('sl-progress-bar')) {
      chartEl.insertAdjacentHTML('afterbegin', '<sl-progress-bar indeterminate></sl-progress-bar>');
    }

    const options = {credentials: 'omit'};
    fetch(url, options).then((res) => res.json()).then((response) => {
      this.drawVisualization(response, this.selectedBucketId, this.showAllHistoricalData);
    });

    const currentUrl = '/metrics/' + this.type + '/timeline/' + this.view + '/' +
              this.selectedBucketId;
    if (history.pushState && location.pathname != currentUrl) {
      history.pushState({id: this.selectedBucketId}, '', currentUrl);
    }
  }

  _renderHTTPArchiveData() {
    const feature = this.props.find((el) => el[0] === parseInt(this.selectedBucketId));
    if (feature) {
      let featureName = feature[1];
      const inputEl = this.shadowRoot.querySelector('#datalist-input');
      inputEl.value = featureName;

      if (this.type == 'css') {
        featureName = convertToCamelCaseFeatureName(featureName);
      }
      const REPORT_ID = '1M8kXOqPkwYNKjJhtag_nvDNJCpvmw_ri';
      const dsEmbedUrl = `https://datastudio.google.com/embed/reporting/${REPORT_ID}/page/tc5b?params=%7B"df3":"include%25EE%2580%25800%25EE%2580%2580IN%25EE%2580%2580${featureName}"%7D`;
      const hadEl = this.shadowRoot.querySelector('#http-archive-data');
      hadEl.src = dsEmbedUrl;

      const bigqueryEl = this.shadowRoot.querySelector('#bigquery');
      bigqueryEl.textContent =`#standardSQL
SELECT yyyymmdd, client, pct_urls, sample_urls
FROM \`httparchive.blink_features.usage\`
WHERE feature = '${featureName}'
ORDER BY yyyymmdd DESC, client`;
    }
  }

  render() {
    return html`
      <input id="datalist-input" type="search" list="features" placeholder="Select or search a property" @change="${this.updateSelectedBucketId}" />
      <datalist id="features">
        ${this.props.map((prop) => html`
          <option value="${prop[1]}" dataset-debug-bucket-id="${prop[0]}"></option>
        `)}
      </datalist>
      <label>
        Show all historical data:
        <input type="checkbox" ?checked="${this.showAllHistoricalData}" @change="${this.toggleShowAllHistoricalData}">
      </label>
      <h3 id="usage" class="header_title">Percentage of page loads over time</h3>
      <p class="description">The chart below shows the percentage of page loads (in Chrome) that use
        this feature at least once. Data is across all channels and platforms.
        Newly added use counters that are not on Chrome stable yet
        only have data from the Chrome channels they're on.
      </p>
      <div id="chart"></div>
      <p class="callout">
        <b>Note</b>: on 2017-10-26 the underlying metrics were switched over to a newer collection system
        which is <a href="https://groups.google.com/a/chromium.org/forum/#!msg/blink-api-owners-discuss/IpIkbz0qtrM/HUCfSMv2AQAJ" target="_blank">more accurate</a>.
        This is also the reason for the abrupt spike around 2017-10-26.
      </p>
      <h3 id="httparchive" class="header_title">Adoption of the feature on top sites</h3>
      <p class="description">The chart below shows the adoption of the feature by the top URLs on the internet. Data from <a href="https://httparchive.org/" target="_blank">HTTP Archive</a>.</p>
      <iframe id="http-archive-data"></iframe>
      <p class="callout">
        <b>Note</b>: The jump around July and December 2018 are because the corpus of URLs crawled by HTTP Archive increased. These jumps have no correlation with the jump in the top graph.
        See the <a href="https://discuss.httparchive.org/t/changes-to-the-http-archive-corpus/1539" target="_blank">announcement</a> for more details.
      </p>
      <p class="description">Copy and run this command in <a href="https://bigquery.cloud.google.com" target="_blank">BigQuery</a> to produce similar results:</p>
      <pre id="bigquery"></pre>
    `;
  }
}


// Capitalizes the first letter of a word.
function capitalize(word) {
  const letters = word.split('');
  letters[0] = letters[0].toUpperCase();
  return letters.join('');
}

// Converts 'background-image' to 'CSSPropertyBackgroundImage'.
function convertToCamelCaseFeatureName(property) {
  return 'CSSProperty' + property.split('-').map(capitalize).join('');
}


customElements.define('chromedash-timeline', ChromedashTimeline);
