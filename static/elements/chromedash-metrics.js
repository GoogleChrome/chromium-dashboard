import {LitElement, html} from 'lit-element';
import '@polymer/iron-icon';
import './chromedash-x-meter';

class ChromedashMetrics extends LitElement {
  static get properties() {
    return {
      type: {type: String}, // From attribute
      view: {type: String}, // From attribute
      prod: {type: Boolean}, // From attibute
      viewList: {type: Array},
      propertyNameSortIcon: {type: String},
      percentSortIcon: {type: String},
      maxPercentage: {type: Number},
    };
  }

  constructor() {
    super();
    this.viewList = [];
    this.type = '';
    this.maxPercentage = 100;
    this.sortOrders = {
      property_name: {reverse: false, activated: false},
      percentage: {reverse: true, activated: true},
    };
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  firstUpdated() {
    const endpoint = `${!this.prod ? 'https://www.chromestatus.com' : ''}/data/${this.type}${this.view}`;
    fetch(endpoint).then((res) => res.json()).then((response) => {
      this._updateAfterData(response);
    });
  }

  _updateAfterData(items) {
    this._fireEvent('app-ready');

    if (!items || !items.length) {
      return;
    }

    for (let i = 0, item; item = items[i]; ++i) {
      item.percentage = (item.day_percentage * 100).toFixed(6);
    }

    this.viewList = items.filter((item) => {
      return !['ERROR', 'PageVisits', 'PageDestruction'].includes(item.property_name);
    });

    this.maxPercentage = this.viewList.reduce((accum, currVal) => {
      return Math.max(accum, currVal.percentage);
    }, 0);

    if (location.hash) {
      const hash = decodeURIComponent(location.hash);
      if (hash) {
        const el = this.$['stack-rank-list'].querySelector(hash);
        el.scrollIntoView(true, {behavior: 'smooth'});
      }
    }
  }

  sort(e) {
    e.preventDefault();

    const order = e.target.dataset.order;
    sortBy_(order, this.viewList);
    switch (order) {
      case 'percentage':
        this.sortOrders.percentage.activated = true;
        this.sortOrders.percentage.reverse = !this.sortOrders.percentage.reverse;
        break;
      case 'property_name':
        this.sortOrders.property_name.activated = true;
        this.sortOrders.property_name.reverse = !this.sortOrders.property_name.reverse;
        break;
    }

    this._updateSortIcons();
    if (this.sortOrders[order].reverse) {
      this.viewList.reverse();
    }

    // TODO: remove when github.com/Polymer/polymer/issues/2175 is fixed.
    this.viewList = this.viewList.slice(0);
  }

  showTimeline(e) {
    window.location.href = `/metrics/${this.type}/timeline/${this.view}/${e.model.prop.bucket_id}`;
  }

  _updateSortIcons() {
    this.propertyNameSortIcon = this._getOrderIcon('property_name');
    this.percentSortIcon = this._getOrderIcon('percentage');
  }

  _getOrderIcon(key) {
    if (!this.sortOrders[key].activated) {
      return '';
    }
    return this.sortOrders[key].reverse ?
      'chromestatus:arrow-drop-up' : 'chromestatus:arrow-drop-down';
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-metrics.css">

      <b>Showing <span>${this.viewList.length}</span> properties</b>
      <ol id="stack-rank-list">
        <li class="header">
          <label @click="${this.sort}" data-order="property_name">
            Property name <iron-icon icon="${this.propertyNameSortIcon}"></iron-icon>
          </label>
          <label @click="${this.sort}" data-order="percentage" class="percent_label">
           Percentage <iron-icon icon="${this.percentSortIcon}"></iron-icon>
          </label>
        </li>
        ${this.viewList.map((item) => html`
          <li id="${item.property_name}"
              title="${item.property_name}. Click to deep link to this property." tabindex="0">
            <label>
              <a href="#${item.property_name}">${item.property_name}</a>
            </label>
            <chromedash-x-meter value="${item.percentage}" max="${this.maxPercentage}" @click="${this.showTimeline}"
                     title="Click to see a timeline view of this property"></chromedash-x-meter>
          </li>
          `)}
      </ol>
    `;
  }
}

customElements.define('chromedash-metrics', ChromedashMetrics);

const sortBy_ = (propName, arr) => {
  const compareAsNumbers = propName === 'percentage' || false;
  arr.sort((a, b) => {
    const propA = compareAsNumbers ? Number(a[propName]) : a[propName];
    const propB = compareAsNumbers ? Number(b[propName]) : b[propName];
    if (propA > propB) {
      return 1;
    }
    if (propA < propB) {
      return -1;
    }
    return 0;
  });
};
