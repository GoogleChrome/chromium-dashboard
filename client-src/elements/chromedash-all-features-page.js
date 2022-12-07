import {LitElement, css, html} from 'lit';
import {openApprovalsDialog} from './chromedash-approvals-dialog';
import {showToastMessage} from './utils.js';
import './chromedash-feature-table';
import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashAllFeaturesPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      css`
      `];
  }

  static get properties() {
    return {
      rawQuery: {type: Object},
      query: {type: String},
      user: {type: Object},
      starredFeatures: {type: Object},
    };
  }

  constructor() {
    super();
    this.query = '';
    this.user = {};
    this.starredFeatures = new Set();
  }

  connectedCallback() {
    super.connectedCallback();
    this.initializeQuery();
    this.fetchData();
  }

  initializeQuery() {
    if (!this.rawQuery) {
      return;
    }

    if (!this.rawQuery.hasOwnProperty('q')) {
      return;
    }
    this.query = this.rawQuery['q'];
  }

  fetchData() {
    window.csClient.getStars().then((starredFeatures) => {
      this.starredFeatures = new Set(starredFeatures);
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  // Handles the Star-Toggle event fired by any one of the child components
  handleStarToggle(e) {
    const newStarredFeatures = new Set(this.starredFeatures);
    window.csClient.setStar(e.detail.featureId, e.detail.doStar)
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

  handleOpenApprovals(e) {
    openApprovalsDialog(this.user, e.detail.feature);
  }

  renderBox(query) {
    return html`
      <chromedash-feature-table
        .query=${query}
        showQuery
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        ?canApprove=${this.user && this.user.can_approve}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        @open-approvals-event=${this.handleOpenApprovals}
        num=100 alwaysOfferPagination columns="normal">
      </chromedash-feature-table>
    `;
  }

  renderFeatureList() {
    return this.renderBox(this.query);
  }

  render() {
    return html`
      <div id="feature-count">
        <h2>Features</h2>
      </div>
      ${this.renderFeatureList()}
    `;
  }
}

customElements.define('chromedash-all-features-page', ChromedashAllFeaturesPage);
