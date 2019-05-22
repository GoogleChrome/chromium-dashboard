import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
import 'https://www.gstatic.com/charts/loader.js'; // Global `google.charts.load`

class ChromedashTimeline extends LitElement {
  static get properties() {
    return {
      selectedBucketId: {type: Number},
      showAllHistoricalData: {type: Boolean},
      timeline: {type: Object}, // Not used?
      title: {type: String},
      type: {type: String},
      view: {type: String},
      props: {type: Array}, // Directly edited from metrics/css/timeline/popularity and metrics/feature/timeline/popularity
      useRemoteData: {type: Boolean}, // If true, fetches live data from chromestatus.com instead of localhost.
    };
  }

  constructor() {
    super();
    this.selectedBucketId = 1;
    this.showAllHistoricalData = false;
    this.title = '';
    this.type = '';
    this.view = '';
    this.props = [];
    this.useRemoteData = false;
  }

  updated(changedProperties) {
    const TRACKING_PROPERTIES = [
      'selectedBucketId',
      'type',
      'view',
      'useRemoteData',
      'showAllHistoricalData',
    ];
    if (TRACKING_PROPERTIES.some((property) => changedProperties.get(property))) {
      this._updateTimeline();
    }
  }

  updateSelectedBucketId(e) {
    this.selectedBucketId = e.currentTarget.value;
  }

  toggleShowAllHistoricalData() {
    this.showAllHistoricalData = !this.showAllHistoricalData;
  }

  ready() {
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.setOnLoadCallback(() => {
      // If there's an id in the URL, load the property it.
      const lastSlash = location.pathname.lastIndexOf('/');
      if (lastSlash > 0) {
        const id = parseInt(location.pathname.substring(lastSlash + 1));
        if (String(id) != 'NaN') {
          this.selectedBucketId = id;
        }
      }
    });
  }

  drawVisualization(data, bucketId, showAllHistoricalData) {
    const table = new google.visualization.DataTable();
    table.addColumn('date', 'Date');
    table.addColumn('number', 'Percentage');
    table.addColumn({type: 'string', role: 'annotation'});
    table.addColumn({type: 'string', role: 'annotationText'});

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

    table.addRows(rowArray);

    table = google.visualization.data.group(table,
      [{column: 0, modifier: new Date(date.getFullYear(), date.getMonth()), type: 'date'}],
      [{
        column: 1,
        aggregation: google.visualization.data.avg,
        type: 'number',
        label: 'Monthly Average',
      }],
      [{column: 2, type: 'string'}]
    );

    const formatter = new google.visualization.NumberFormat({fractionDigits: 6});
    formatter.format(table, 1); // Apply formatter to percentage column.

    let view = table;

    if (!showAllHistoricalData) {
      const startYear = (new Date()).getFullYear() - 2; // Show only 2 years of data by default.
      view = new google.visualization.DataView(table);
      view.setRows(view.getFilteredRows([{column: 0, minValue: new Date(startYear, 0, 1)}]));
    }

    const chart = new google.visualization.LineChart(this.$.chart);
    chart.draw(view, {
      // title: this.title,
      // subtitle: 'all channels and platforms',
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
        format: 'M/yy',
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
    if (this.selectedBucketId === 1) {
      return;
    }

    const prefix = this.useRemoteData ? 'https://www.chromestatus.com' : '';

    const url = prefix + '/data/timeline/' + this.type + this.view +
              '?bucket_id=' + this.selectedBucketId;

    this._renderHTTPArchiveData();

    fetch(url).then((res) => res.json()).then((response) => {
      this.drawVisualization(response, this.selectedBucketId, this.showAllHistoricalData);
    });

    if (history.pushState) {
      const url = '/metrics/' + this.type + '/timeline/' + this.view + '/' +
                this.selectedBucketId;
      history.pushState({id: this.selectedBucketId}, '', url);
    }
  }

  _renderHTTPArchiveData() {
    if (!this.props.length) {
      return;
    }

    const feature = this.props.find((el) => el[0] === parseInt(this.selectedBucketId));
    if (feature) {
      const featureName = feature[1];
      const REPORT_ID = '1M8kXOqPkwYNKjJhtag_nvDNJCpvmw_ri';
      const dsEmbedUrl = `https://datastudio.google.com/embed/reporting/${REPORT_ID}/page/tc5b?config=%7B"df3":"include%25EE%2580%25800%25EE%2580%2580IN%25EE%2580%2580${featureName}"%7D`;
      this.$.httparchivedata.src = dsEmbedUrl;

      this.$.bigquery.textContent = `#standardSQL
SELECT yyyymmdd, client, pct_urls, sample_urls
FROM \`httparchive.blink_features.usage\`
WHERE feature = '${featureName}'
ORDER BY yyyymmdd DESC, client`;
    }
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-timeline.css">

      <select .value="${this.selectedBucketId}" @change="${this.updateSelectedBucketId}">
        <option disabled value="1">Select a property</option>
        ${this.props.map((prop) => html`
          <option value="${prop[0]}">${prop[1]}</option>
          `)}
      </select>
      <label>Show all historical data: <input type="checkbox" ?checked="${this.showAllHistoricalData}" @change="${this.toggleShowAllHistoricalData}"></label>
      <h3 id="usage" class="header_title">Percentage of page loads that use this feature</h3>
      <p class="description">The chart below shows the percentage of page loads (in Chrome) that use
        this feature at least once. Data is across all channels and platforms.
      </p>
      <div id="chart"></div>
      <p class="callout">
        <b>Note</b>: on 2017-10-26 the underlying metrics were switched over to a newer collection system
        which is <a href="https://groups.google.com/a/chromium.org/forum/#!msg/blink-api-owners-discuss/IpIkbz0qtrM/HUCfSMv2AQAJ" target="_blank">more accurate</a>.
        This is also the reason for the abrupt spike around 2017-10-26.
      </p>
      <h3 id="httparchive" class="header_title">Adoption of the feature on top sites</h3>
      <p class="description">The chart below shows the adoption of the feature by the top URLs on the internet. Data from <a href="https://httparchive.org/" target="blank">HTTP Archive</a>.</p>
      <iframe id="httparchivedata"></iframe>
      <p class="callout">
        <b>Note</b>: The jump around July and December 2018 are because the corpus of URLs crawled by HTTP Archive increased. These jumps have no correlation with the jump in the top graph.
        See the <a href="https://discuss.httparchive.org/t/changes-to-the-http-archive-corpus/1539" target="_blank">announcement</a> for more details.
      </p>
      <p class="description">Copy and run this command in <a href="https://bigquery.cloud.google.com" target="_blank">BigQuery</a> to produce similar results:</p>
      <pre id="bigquery"></pre>
    `;
  }
}

customElements.define('chromedash-timeline', ChromedashTimeline);
