import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage} from './utils.js';
import './chromedash-feature-table';
import {SHARED_STYLES} from '../css/shared-css.js';

export class ChromedashAllFeaturesPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      css`
        #content-title {
          padding-top: var(--content-padding);
        }
      `,
    ];
  }

  static get properties() {
    return {
      rawQuery: {type: Object},
      title: {type: String},
      showQuery: {type: Boolean},
      query: {type: String},
      columns: {type: String},
      showEnterprise: {type: Boolean},
      sortSpec: {type: String},
      user: {type: Object},
      start: {type: Number},
      num: {type: Number},
      starredFeatures: {type: Object},
      selectedGateId: {type: Number},
    };
  }

  constructor() {
    super();
    this.title = 'Features';
    this.showQuery = true;
    this.query = '';
    this.columns = 'normal';
    this.sortSpec = '';
    this.showEnterprise = false;
    this.user = {};
    this.start = 0;
    this.num = 100;
    this.starredFeatures = new Set();
    this.selectedGateId = 0;
  }

  connectedCallback() {
    super.connectedCallback();
    this.initializeParams();
    this.fetchData();
  }

  initializeParams() {
    if (!this.rawQuery) {
      return;
    }

    if (this.rawQuery.hasOwnProperty('q')) {
      this.query = this.rawQuery['q'];
    }
    if (this.rawQuery.hasOwnProperty('columns')) {
      this.columns = this.rawQuery['columns'];
    }
    if (this.rawQuery.hasOwnProperty('showEnterprise')) {
      this.showEnterprise = true;
    }
    if (this.rawQuery.hasOwnProperty('sort')) {
      this.sortSpec = this.rawQuery['sort'];
    }
    if (
      this.rawQuery.hasOwnProperty('start') &&
      !Number.isNaN(parseInt(this.rawQuery['start']))
    ) {
      this.start = parseInt(this.rawQuery['start']);
    }
    if (
      this.rawQuery.hasOwnProperty('num') &&
      !Number.isNaN(parseInt(this.rawQuery['num']))
    ) {
      this.num = parseInt(this.rawQuery['num']);
    }
  }

  fetchData() {
    window.csClient
      .getStars()
      .then(starredFeatures => {
        this.starredFeatures = new Set(starredFeatures);
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  refetch() {
    const tables = this.shadowRoot.querySelectorAll('chromedash-feature-table');
    for (const table of tables) {
      table.refetch();
    }
  }

  // Handles the Star-Toggle event fired by any one of the child components
  handleStarToggle(e) {
    const newStarredFeatures = new Set(this.starredFeatures);
    window.csClient
      .setStar(e.detail.featureId, e.detail.doStar)
      .then(() => {
        if (e.detail.doStar) {
          newStarredFeatures.add(e.detail.featureId);
        } else {
          newStarredFeatures.delete(e.detail.featureId);
        }
        this.starredFeatures = newStarredFeatures;
      })
      .catch(() => {
        alert('Unable to star the Feature. Please Try Again.');
      });
  }

  renderFeatureList() {
    return html`
      <chromedash-feature-table
        .query=${this.query}
        ?showEnterprise=${this.showEnterprise}
        .sortSpec=${this.sortSpec}
        .start=${this.start}
        .num=${this.num}
        ?showQuery=${this.showQuery}
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        selectedGateId=${this.selectedGateId}
        alwaysOfferPagination
        columns=${this.columns}
      >
      </chromedash-feature-table>
    `;
  }

  render() {
    const adminNotice =
      this.user?.is_admin && this.columns === 'approvals'
        ? html`<p>
            You see all pending approvals because you're a site admin.
          </p>`
        : nothing;

    return html`
      <div id="content-title">
        <h2>${this.title}</h2>
      </div>
      ${adminNotice} ${this.renderFeatureList()}
    `;
  }
}

customElements.define(
  'chromedash-all-features-page',
  ChromedashAllFeaturesPage
);
