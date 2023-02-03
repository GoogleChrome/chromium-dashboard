import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import './chromedash-x-meter';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashStackRank extends LitElement {
  static get properties() {
    return {
      type: {type: String},
      view: {type: String},
      viewList: {attribute: false},
      maxPercentage: {attribute: false},
      sortType: {type: String},
      sortReverse: {type: Boolean},
      tempList: {attribute: false},
    };
  }

  constructor() {
    super();
    this.type = '';
    this.viewList = [];
    this.tempList = [];
    this.maxPercentage = 100;
    this.sortType = 'percentage';
    this.sortReverse = false;
  }


  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: block;
        flex: 1;
        padding: 1px;
      }

      .title-text {
        flex: 1;
        font-weight: 500;
      }

      li {
        padding: 5px 0;
        display: flex;
        align-items: center;
      }

      #subheader {
        font-size: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      #dropdown-selection:hover {
        background: var(--md-gray-100-alpha);
      }

      sl-button::part(base) {
        color: #000;
      }

      li > :first-child {
        flex: 1;
        word-break: break-all;
      }

      li > :nth-child(2) {
        flex: 2;
      }

      .stack-rank-header {
        margin-bottom: 5px;
        text-align: center;
      }

      .stack-rank-item {
        border-top: var(--table-divider)
      }

      .stack-rank-item-name {
        display: grid;
        grid-template-columns: var(--icon-size) 1fr;
        grid-column-gap: 15px;
        position: relative;
        left: -20px;
      }
      .stack-rank-item-name .hash-link {
        place-self: center;
        visibility: hidden;
      }
      .stack-rank-item-name:hover .hash-link {
        visibility: visible;
      }

      .stack-rank-item-result {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-right: 15px;
      }

      chromedash-x-meter {
        flex: 1;
      }

      a.icon-wrapper {
        display: flex;
        gap: 3px;
        align-items: center;
      }
      a.icon-wrapper:hover {
        text-decoration: none;
      }

      .spacer {
        visibility: hidden;
      }

      sl-skeleton {
        margin: 0;
        padding: 5px 20px;
      }

      /* On small displays, only show timeline icons (no text). */
      @media only screen and (max-width: 600px) {
        .icon-text {
          display: none;
        }

        .stack-rank-item-name {
          grid-column-gap: 5px;
        }

        .stack-rank-item-result {
          margin-right: 5px;
        }
    `];
  }

  willUpdate(changedProperties) {
    if (!changedProperties.has('viewList') || !this.viewList.length) return;

    this.maxPercentage = this.viewList.reduce((accum, currVal) => {
      return Math.max(accum, currVal.percentage);
    }, 0);
    setTimeout(() => {
      this.scrollToPosition();
    }, 300);
  }

  scrollToPosition(e) {
    let hash;
    if (e) {
      hash = e.currentTarget.getAttribute('href');
    } else if (location.hash) {
      hash = decodeURIComponent(location.hash);
    }

    if (hash) {
      const el = this.shadowRoot.querySelector('.stack-rank-list ' + hash);
      el.scrollIntoView(true, {behavior: 'smooth'});
    }
  }

  sort(e) {
    e.preventDefault();

    const parts = e.target.dataset.order.split('-');
    this.sortType = parts[0];
    this.sortReverse = Boolean(parts[1]);

    const newViewList = [...this.viewList];
    this.viewList = sortBy_(this.sortType, this.sortReverse, newViewList);
  }

  renderSubHeader() {
    return html`
      <div id="subheader">
        <p class="title-text">Showing <span>${this.viewList.length}</span> properties</p>
        <div id="dropdown-selection">
          <sl-dropdown>
            <sl-button slot="trigger" variant="text" ?disabled=${!this.viewList.length}>
              <iron-icon icon="chromestatus:sort"></iron-icon>
              SORT BY
            </sl-button>
            <sl-menu @click="${this.sort}">
              <sl-menu-item type="checkbox"
                ?checked=${this.sortType == 'percentage' && !this.sortReverse}
                data-order="percentage">
                Most used
              </sl-menu-item>
              <sl-menu-item type="checkbox"
                ?checked=${this.sortType == 'percentage' && this.sortReverse}
                data-order="percentage-reverse">
                Least used
              </sl-menu-item>
              <sl-menu-item type="checkbox"
                ?checked=${this.sortType == 'property_name' && this.sortReverse}
                data-order="property_name-reverse">
                Name (A-Z)
              </sl-menu-item>
              <sl-menu-item type="checkbox"
                ?checked=${this.sortType == 'property_name' && !this.sortReverse}
                data-order="property_name">
                Name (Z-A)
              </sl-menu-item>
            </sl-menu>
          </sl-dropdown>
        </div>
      </div>
    `;
  }

  renderStackRank(displayedList) {
    return html`
      ${displayedList.map((item) => html`
        <li class="stack-rank-item" id="${item.property_name}">
          <div title="${item.property_name}. Click to deep link to this property.">
            <a class="stack-rank-item-name" href="#${item.property_name}" @click=${this.scrollToPosition}>
              <iron-icon class="hash-link" icon="chromestatus:link"></iron-icon>
              <p>${item.property_name}</p>
            </a>
          </div>
          <div class="stack-rank-item-result">
            <chromedash-x-meter
              value="${item.percentage}"
              max="${this.maxPercentage}"
              href="/metrics/${this.type}/timeline/${this.view}/${item.bucket_id}"
              title="Click to see a timeline view of this property">
            </chromedash-x-meter>
            <a class="icon-wrapper"
              href="/metrics/${this.type}/timeline/${this.view}/${item.bucket_id}"
              title="Click to see a timeline view of this property">
              <iron-icon icon="chromestatus:timeline"></iron-icon>
              <p class="icon-text">Timeline</p>
            </a>
          </div>
        </li>
      `)}
    `;
  }

  renderSkeletons() {
    return html`${Array.from(Array(20)).map(() => html`
      <li class="stack-rank-item">
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
      </li>
    `)}`;
  }

  renderTemporaryRank() {
    return html`
      ${this.tempList.length ? this.renderStackRank(this.tempList) : nothing}
      ${this.renderSkeletons()}
    `;
  }

  renderStackRankList() {
    return html`
      <ol class="stack-rank-list">
        <li class="stack-rank-header">
          <p class="title-text">Property name</p>
          <div class="stack-rank-item-result">
            <p class="title-text">Percentage</p>
            <a class="icon-wrapper spacer">
              <iron-icon icon="chromestatus:timeline"></iron-icon>
              <p class="icon-text">Timeline</p>
            </a>
          </div>
        </li>
        ${this.viewList.length ? this.renderStackRank(this.viewList) : this.renderTemporaryRank()}
      </ol>
    `;
  }

  render() {
    return html`
      ${this.renderSubHeader()}
      ${this.renderStackRankList()}
    `;
  }
}

customElements.define('chromedash-stack-rank', ChromedashStackRank);

const sortBy_ = (propName, reverse, arr) => {
  const compareAsNumbers = propName === 'percentage';
  arr.sort((a, b) => {
    const propA = compareAsNumbers ? Number(a[propName]) : a[propName];
    const propB = compareAsNumbers ? Number(b[propName]) : b[propName];
    if (propA > propB) {
      return reverse ? 1 : -1;
    }
    if (propA < propB) {
      return reverse ? -1 : 1;
    }
    return 0;
  });
  return arr;
};
