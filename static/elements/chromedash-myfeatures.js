import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';

class ChromedashMyFeatures extends LitElement {
  static get properties() {
    return {
      signedIn: {type: Boolean},
      canEdit: {type: Boolean},
      canApprove: {type: Boolean},
      loginUrl: {type: String},
      starredFeatures: {type: Object}, // will contain a set of starred features
    };
  }

  constructor() {
    super();
    this.starredFeatures = new Set();
    this.canEdit = false;
    this.canApprove = false;
  }

  // Handles the Star-Toggle event fired by any one of the child components
  handleStarToggle(e) {
    const newStarredFeatures = new Set(this.starredFeatures);
    window.csClient.setStar(e.detail.feature, e.detail.doStar)
      .then(() => {
        if (e.detail.doStar) {
          newStarredFeatures.add(e.detail.feature);
        } else {
          newStarredFeatures.delete(e.detail.feature);
        }
        this.starredFeatures = newStarredFeatures;
      })
      .catch(() => {
        alert('Unable to star the Feature. Please Try Again.');
      });
  }


  renderBox(title, query, columns) {
    return html`
      <chromedash-accordion
        title="${title}"
        opened>

        <chromedash-feature-table
          query="${query}"
          ?signedin=${this.signedIn}
          ?canedit=${this.canEdit}
          ?canApprove=${this.canApprove}
          .starredFeatures=${this.starredFeatures}
          @star-toggle-event=${this.handleStarToggle}
          rows=10 columns=${columns}>
        </chromedash-feature-table>
      </chromedash-accordion>
    `;
  }

  renderPendingApprovals() {
    return this.renderBox(
      'Features pending my approval', 'pending-approval-by:me', 'approvals');
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
      ${this.canApprove ? this.renderPendingApprovals() : nothing}
      ${this.renderIStarred()}
      ${this.renderIOwn()}
    `;
  }
}

customElements.define('chromedash-myfeatures', ChromedashMyFeatures);
