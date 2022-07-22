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
      user: {type: Object},
      starredFeatures: {type: Object},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.starredFeatures = new Set();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    Promise.all([
      window.csClient.getPermissions(),
      window.csClient.getStars(),
    ]).then(([user, starredFeatures]) => {
      this.user = user;
      this.starredFeatures = new Set(starredFeatures);

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
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
    openApprovalsDialog(this.signedInUser, e.detail.feature);
  }

  renderBox(query) {
    return html`
      <chromedash-feature-table
        query="${query}"
        showQuery
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        ?canApprove=${this.user && this.user.can_approve}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        @open-approvals-event=${this.handleOpenApprovals}
        rows=100 columns="normal">
      </chromedash-feature-table>
    `;
  }

  renderFeatureList() {
    return this.renderBox('');
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
