import {LitElement, css, html} from 'lit';
import './chromedash-approvals-dialog';
import './chromedash-feature-table';
import SHARED_STYLES from '../css/shared.css';


class ChromedashNewFeatureList extends LitElement {
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
      SHARED_STYLES,
      css`
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

  renderBox(query) {
    return html`
        <chromedash-feature-table
          query="${query}"
          showQuery="true"
          ?signedIn=${Boolean(this.signedInUser)}
          ?canEdit=${this.canEdit}
          ?canApprove=${this.canApprove}
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
      ${this.renderFeatureList()}
      <chromedash-approvals-dialog
        .signedInUser=${this.signedInUser}
      ></chromedash-approvals-dialog>
    `;
  }
}

customElements.define('chromedash-new-feature-list', ChromedashNewFeatureList);
