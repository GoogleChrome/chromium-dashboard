import {LitElement, css, html, nothing} from 'lit';
import './chromedash-feature-table';
import {openApprovalsDialog} from './chromedash-approvals-dialog';
import {showToastMessage} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashMyFeaturesPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-details {
          padding: 0 var(--content-padding);
        }
      `];
  }

  static get properties() {
    return {
      user: {type: Object},
      starredFeatures: {attribute: false}, // will contain a set of starred features
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
        showToastMessage('Unable to star the Feature. Please Try Again.');
      });
  }

  handleOpenApprovals(e) {
    openApprovalsDialog(this.user.email, e.detail.feature);
  }

  renderBox(title, query, columns, opened=true) {
    return html`
      <sl-details
        summary="${title}"
        ?open=${opened}>

        <chromedash-feature-table
          query="${query}"
          ?signedIn=${Boolean(this.user)}
          ?canEdit=${this.user && this.user.can_edit_all}
          ?canApprove=${this.user && this.user.can_approve}
          .starredFeatures=${this.starredFeatures}
          @star-toggle-event=${this.handleStarToggle}
          @open-approvals-event=${this.handleOpenApprovals}
          rows=10 columns=${columns}>
        </chromedash-feature-table>
      </sl-details>
    `;
  }

  renderPendingAndRecentApprovals() {
    const pendingBox = this.renderBox(
      'Features pending my approval', 'pending-approval-by:me', 'approvals');
    const recentBox = this.renderBox(
      'Recently reviewed features', 'is:recently-reviewed', 'normal', false);
    return [pendingBox, recentBox];
  }

  renderIStarred() {
    return this.renderBox(
      'Features I starred', 'starred-by:me', 'normal');
  }

  renderIOwn() {
    return this.renderBox(
      'Features I own', 'owner:me', 'normal');
  }

  renderICanEdit() {
    return this.renderBox(
      'Features I can edit', 'editor:me', 'normal');
  }

  render() {
    return html`
      <div id="subheader">
        <h2>My features</h2>
      </div>
      ${this.user && this.user.can_approve ? this.renderPendingAndRecentApprovals() : nothing}
      ${this.renderIOwn()}
      ${this.renderICanEdit()}
      ${this.renderIStarred()}
    `;
  }
}

customElements.define('chromedash-myfeatures-page', ChromedashMyFeaturesPage);
