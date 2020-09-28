import {LitElement, css, html} from 'lit-element';
import {ifDefined} from 'lit-html/directives/if-defined.js';

import '@polymer/iron-icon';
import './chromedash-x-meter';
import SHARED_STYLES from '../css/shared.css';

class ChromedashMetrics extends LitElement {
  static get properties() {
    return {
      type: {type: String},
      view: {type: String},
      prod: {type: Boolean},
      viewList: {attribute: false},
      propertyNameSortIcon: {attribute: false},
      percentSortIcon: {attribute: false},
      maxPercentage: {attribute: false},
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


  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        display: block;
        flex: 1;
        padding: 1px;
      }

      .stack-rank-list {
        margin: 0;
        padding: 0;
      }

      li {
          margin: 0;
          padding: 5px 0;
          display: flex;
          align-items: center;
      }

      .stack-rank-list label {
        font-weight: 500;
      }

      li > :first-child {
        flex: 1;
        margin-right: 10px;
      }

      li > :nth-child(2) {
        flex: 2;
      }

      li.header {
        margin-bottom: 10px;
      }

      chromedash-x-meter {
        margin-left: 7px;
        cursor: pointer;
      }
    `];
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  async firstUpdated() {
    const endpoint = `${!this.prod ? 'https://www.chromestatus.com' : ''}/data/${this.type}${this.view}`;
    const res = await fetch(endpoint);
    const json = await res.json();
    this._updateAfterData(json);
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
    setTimeout(() => {
      this._scrollToInitialPosition();
    }, 300);
  }

  _scrollToInitialPosition() {
    if (location.hash) {
      const hash = decodeURIComponent(location.hash);
      if (hash) {
        const el = this.shadowRoot.querySelector('.stack-rank-list ' + hash);
        el.scrollIntoView(true, {behavior: 'smooth'});
      }
    }
  }

  sort(e) {
    e.preventDefault();

    const order = e.currentTarget.dataset.order;
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
      <b>Showing <span>${this.viewList.length}</span> properties</b>
      <ol class="stack-rank-list">
        <li class="header">
          <span @click="${this.sort}" data-order="property_name">
            Property name <iron-icon icon="${ifDefined(this.propertyNameSortIcon)}"></iron-icon>
          </span>
          <span @click="${this.sort}" data-order="percentage" class="percent_label">
           Percentage <iron-icon icon="${ifDefined(this.percentSortIcon)}"></iron-icon>
          </span>
        </li>
        ${this.viewList.map((item) => html`
          <li id="${item.property_name}"
              title="${item.property_name}. Click to deep link to this property." tabindex="0">
            <a href="#${item.property_name}">${item.property_name}</a>
            <chromedash-x-meter value="${item.percentage}" max="${this.maxPercentage}"
                href="/metrics/${this.type}/timeline/${this.view}/${item.bucket_id}"
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
