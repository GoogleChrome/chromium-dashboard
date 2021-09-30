import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import SHARED_STYLES from '../css/shared.css';

class ChromedashFeatureTable extends LitElement {
  static get properties() {
    return {
      query: {type: String},
      features: {type: Array},
      loading: {type: Boolean},
      rows: {type: Number},
      columns: {type: String},
      signedIn: {type: Boolean},
      canEdit: {type: Boolean},
      canApprove: {type: Boolean},
      starredFeatures: {type: Object},
      noResultsMessage: {type: String},
    };
  }

  constructor() {
    super();
    this.loading = true;
    this.starredFeatures = new Set();
    this.features = [];
    this.noResultsMessage = 'No results';
    this.canEdit = false;
    this.canApprove = false;
  }

  connectedCallback() {
    super.connectedCallback();
    window.csClient.searchFeatures(this.query).then((features) => {
      this.features = features;
      this.loading = false;
    });
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      table {
        width: var(--max-content-width);
      }
      tr {
        background: var(--table-row-background);
      }
      td {
        padding: var(--content-padding-half);
        border-bottom: var(--table-divider);
      }
      td.name_col {
        width: 100%;
      }
      td.icon_col {
        white-space: nowrap;
      }
      iron-icon {
        --iron-icon-height: 18px;
        --iron-icon-width: 18px;
        color: var(--link-color);
      }
      iron-icon:hover {
        color: var(--link-hover-color);
      }
    `];
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  toggleStar(e) {
    console.log('toggleStar');
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = Number(iconEl.dataset.featureId);
    const newStarred = !this.starredFeatures.has(featureId);

    // handled in myfeatures-page.js
    this._fireEvent('star-toggle-event', {
      feature: featureId,
      doStar: newStarred,
    });
  }

  renderMessages() {
    if (this.loading) {
      return html`
        <tr><td>Loading...</td></tr>
      `;
    }
    if (this.features.length == 0) {
      return html`
        <tr><td>${this.noResultsMessage}</td></tr>
      `;
    }
    return nothing;
  }

  openApprovalsDialog(feature) {
    alert('TODO show approvals for ' + feature.id);
  }

  renderApprovalsIcon(feature) {
    return html`
      <a href="#" class="tooltip"
        @click="${() => this.openApprovalsDialog(feature)}"
        title="Review approvals">
        <iron-icon icon="chromestatus:approval"></iron-icon>
      </span>
    `;
  }

  renderEditIcon(feature) {
    return html`
      <a href="/guide/edit/${feature.id}" class="tooltip"
        title="Edit feature">
        <iron-icon icon="chromestatus:create"></iron-icon>
      </span>
    `;
  }

  renderStarIcon(feature) {
    return html`
      <span class="tooltip"
        title="Receive an email notification when there are updates">
        <iron-icon
          icon="${this.starredFeatures.has(Number(feature.id)) ?
          'chromestatus:star' :
          'chromestatus:star-border'}"
          class="pushicon"
          data-feature-id="${feature.id}"
          @click="${this.toggleStar}">
        </iron-icon>
      </span>
    `;
  }

  renderSignedOutStarIcon() {
    return html`
      <span class="tooltip"
        title="Sign in to get email notifications for updates">
        <a href="#"  @click="${window.promptSignIn}" data-tooltip>
          <iron-icon icon="chromestatus:star-border"
            class="pushicon">
          </iron-icon>
        </a>
      </span>
    `;
  }

  renderIcons(feature) {
    if (this.signedIn) {
      return html`
        ${this.canApprove ? this.renderApprovalsIcon(feature) : nothing}
        ${this.canEdit ? this.renderEditIcon(feature) : nothing}
        ${this.renderStarIcon(feature)}
      `;
    } else {
      return html`
        ${this.renderSignedOutStarIcon()}
      `;
    }
  }

  renderFeature(feature) {
    return html`
      <tr>
        <td class="name_col">
          <a href="/feature/${feature.id}">${feature.name}</a>
        </td>
        <td class="icon_col">
          ${this.renderIcons(feature)}
        </td>
      </tr>
    `;
  }

  render() {
    return html`
      <table>
        ${this.features.map(this.renderFeature.bind(this))}
        ${this.renderMessages()}
      </table>
    `;
  }
}

customElements.define('chromedash-feature-table', ChromedashFeatureTable);
