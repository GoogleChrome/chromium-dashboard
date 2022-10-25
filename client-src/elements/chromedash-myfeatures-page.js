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
        showToastMessage('Unable to star the Feature. Please Try Again.');
      });
  }

  handleOpenApprovals(e) {
    openApprovalsDialog(this.user, e.detail.feature);
  }

  renderBox(title, query, columns, sortSpec='', opened=true) {
    return html`
      <sl-details
        summary="${title}"
        ?open=${opened}>

        <chromedash-feature-table
          query="${query}"
          sortSpec="${sortSpec}"
          ?signedIn=${Boolean(this.user)}
          ?canEdit=${this.user && this.user.can_edit_all}
          ?canApprove=${this.user && this.user.can_approve}
          .starredFeatures=${this.starredFeatures}
          @star-toggle-event=${this.handleStarToggle}
          @open-approvals-event=${this.handleOpenApprovals}
          num=25 columns=${columns}>
        </chromedash-feature-table>
      </sl-details>
    `;
  }

  renderPendingAndRecentApprovals() {
    const pendingBox = this.renderBox(
      'Features pending my approval', 'pending-approval-by:me', 'approvals',
      'approvals.requested_on');
    const recentBox = this.renderBox(
      'Recently reviewed features', 'is:recently-reviewed', 'normal',
      '-approvals.reviewed_on', false);
    return [pendingBox, recentBox];
  }

  renderIStarred() {
    return this.renderBox(
      'Features I starred', 'starred-by:me', 'normal');
  }

  renderICanEdit() {
    return this.renderBox(
      'Features I can edit', 'can_edit:me', 'normal');
  }

  render() {
    return html`
      <div id="subheader">
        <h2>My features</h2>
      </div>
      ${this.user && this.user.can_approve ? this.renderPendingAndRecentApprovals() : nothing}
      ${this.renderICanEdit()}
      ${this.renderIStarred()}
    `;
  }
}

customElements.define('chromedash-myfeatures-page', ChromedashMyFeaturesPage);
