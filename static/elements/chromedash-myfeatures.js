import {LitElement, css, html, nothing} from 'lit';
import './chromedash-accordion';
import './chromedash-approvals-dialog';
import './chromedash-feature-table';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashMyFeatures extends LitElement {
  static get properties() {
    return {
      signedInUser: {type: String},
      canEdit: {type: Boolean},
      canApprove: {type: Boolean},
      loginUrl: {type: String},
      starredFeatures: {type: Object}, // will contain a set of starred features
    };
  }

  constructor() {
    super();
    this.signedInUser = ''; // email address
    this.starredFeatures = new Set();
    this.canEdit = false;
    this.canApprove = false;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        chromedash-accordion {
          padding: 0 var(--content-padding);
        }
      `];
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
    const featureId = e.detail.featureId;
    const dialog = this.shadowRoot.querySelector('chromedash-approvals-dialog');
    dialog.openWithFeature(featureId);
  }

  renderBox(title, query, columns, opened=true) {
    return html`
      <chromedash-accordion
        title="${title}"
        ?opened=${opened}>

        <chromedash-feature-table
          query="${query}"
          ?signedIn=${Boolean(this.signedInUser)}
          ?canEdit=${this.canEdit}
          ?canApprove=${this.canApprove}
          .starredFeatures=${this.starredFeatures}
          @star-toggle-event=${this.handleStarToggle}
          @open-approvals-event=${this.handleOpenApprovals}
          rows=10 columns=${columns}>
        </chromedash-feature-table>
      </chromedash-accordion>
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

  render() {
    return html`
      ${this.canApprove ? this.renderPendingAndRecentApprovals() : nothing}
      ${this.renderIOwn()}
      ${this.renderIStarred()}
      <chromedash-approvals-dialog
        .signedInUser=${this.signedInUser}
      ></chromedash-approvals-dialog>
    `;
  }
}

customElements.define('chromedash-myfeatures', ChromedashMyFeatures);
