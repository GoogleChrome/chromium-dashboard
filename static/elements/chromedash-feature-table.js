import {LitElement, css, html, nothing} from 'lit';
import SHARED_STYLES from '../css/shared.css';
import {STATE_NAMES} from './chromedash-approvals-dialog.js';

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
      approvals: {type: Object},
      comments: {type: Object},
      configs: {type: Object},
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
    this.approvals = {};
    this.comments = {};
    this.configs = {};
  }

  connectedCallback() {
    super.connectedCallback();
    window.csClient.searchFeatures(this.query).then((features) => {
      this.features = features;
      this.loading = false;
      if (this.columns == 'approvals') {
        this.loadApprovalData();
      }
    });
  }

  loadApprovalData() {
    for (const feature of this.features) {
      window.csClient.getApprovals(feature.id).then(res => {
        const newApprovals = {...this.approvals};
        newApprovals[feature.id] = res.approvals;
        this.approvals = newApprovals;
      });
      window.csClient.getComments(feature.id).then(res => {
        const newComments = {...this.comments};
        newComments[feature.id] = res.comments;
        this.comments = newComments;
      });
      window.csClient.getApprovalConfigs(feature.id).then(res => {
        const newConfigs = {...this.configs};
        newConfigs[feature.id] = res.configs;
        this.configs = newConfigs;
      });
    }
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
        vertical-align: top;
      }
      .quick_actions {
        white-space: nowrap;
        float: right;
      }
      .highlights {
        padding-left: var(--content-padding);
      }
      .highlights div {
        color: var(--unimportant-text-color);
        padding: var(--content-padding-quarter);
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }
      iron-icon {
        --iron-icon-height: 18px;
        --iron-icon-width: 18px;
        color: var(--link-color);
      }
      iron-icon:hover {
        color: var(--link-hover-color);
      }
      button {
        border: var(--default-border);
        padding: 0 6px;
        font-size: var(--button-small-font-size);
      }
    `];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
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

    // handled in chromedash-myfeatures.js
    this._fireEvent('star-toggle-event', {
      featureId: featureId,
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

  openApprovalsDialog(featureId) {
    // handled in chromedash-myfeatures.js
    this._fireEvent('open-approvals-event', {
      featureId: featureId,
    });
  }

  doLGTM(featureId) {
    // TODO(jrobbins): Make it pre-select Approved and add comment.
    this.openApprovalsDialog(featureId);
  }

  doSnooze(featureId) {
    // TODO(jrobbins): Make it pre-set a new next-review-date value.
    this.openApprovalsDialog(featureId);
  }

  renderApprovalsIcon(feature) {
    return html`
      <a href="#" class="tooltip"
        @click="${() => this.openApprovalsDialog(feature.id)}"
        title="Review approvals">
        <iron-icon icon="chromestatus:approval"></iron-icon>
      </a>
    `;
  }

  renderEditIcon(feature) {
    return html`
      <a href="/guide/edit/${feature.id}" class="tooltip"
        title="Edit feature">
        <iron-icon icon="chromestatus:create"></iron-icon>
      </a>
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

  renderIcons(feature) {
    if (this.signedIn) {
      return html`
        ${this.canApprove ? this.renderApprovalsIcon(feature) : nothing}
        ${this.canEdit ? this.renderEditIcon(feature) : nothing}
        ${this.renderStarIcon(feature)}
      `;
    } else {
      return nothing;
    }
  }

  renderQuickActions(feature) {
    if (this.columns == 'approvals') {
      // TODO(jrobbins): Show only thread link for active intent.
      // Blocked on merge of PR that adds fetching that info.
      // Work around unused function parameter lint error.
      const threadLinks = feature ? [] : [];

      // TODO(jrobbins): Show these buttons when they work.
      // let lgtmButton = html`
      //  <button data-feature-id="${feature.id}"
      //          @click="${() => this.doLGTM(feature.id)}">
      //    Add LGTM
      //  </button>
      // `;
      // let snoozeButton = html`
      //  <button data-feature-id="${feature.id}"
      //          @click="${() => this.doSnooze(feature.id)}">
      //    Snooze
      //  </button>
      // `;

      return html`
        <span class="quick_actions">
          ${threadLinks}
        </span>
      `;
    }
    return nothing;
  }

  getEarliestReviewDate(feature) {
    const featureConfigs = this.configs[feature.id] || [];
    const allDates = featureConfigs.map(c => c.next_action).filter(d => d);
    if (allDates.length > 0) {
      allDates.sort();
      return allDates[0];
    }
    return null;
  }

  getActiveOwners(feature) {
    const featureConfigs = this.configs[feature.id] || [];
    const allOwners = featureConfigs.map(c => c.owners).flat();
    // TODO(jrobbins): Limit to only owners of active intents
    let activeOwners = allOwners;
    activeOwners = [...new Set(activeOwners)]; // de-dup.
    activeOwners.sort();
    return activeOwners;
  }

  getActiveApprovals(feature) {
    const featureApprovals = this.approvals[feature.id];
    // TODO(jrobbins): Limit to only owners of active intents
    const activeApprovals = featureApprovals;
    return activeApprovals;
  }

  getRecentComment(feature) {
    // TODO(jrobbins): implement this.
    return feature ? null : null;
  }

  renderApprovalsSoFar(approvals) {
    const result = [];
    for (const stateItem of STATE_NAMES) {
      const state = stateItem[0];
      const stateName = stateItem[1];
      const approvalsWithThatState = approvals.filter(a => a.state == state);
      const setters = approvalsWithThatState.map(a => a.set_by.split('@')[0]);
      if (setters.length > 0) {
        result.push(html`<span>${stateName}: ${setters.join(', ')}. </span>`);
      }
    }
    return result;
  }

  renderHighlights(feature) {
    if (this.columns == 'approvals') {
      const nextReviewDate = this.getEarliestReviewDate(feature);
      const owners = this.getActiveOwners(feature);
      const activeApprovals = this.getActiveApprovals(feature);
      const recentComment = this.getRecentComment(feature);
      // TODO(jrobbins): show additional_review.

      return html`
        <div class="highlights">
          ${nextReviewDate ? html`
            <div>
              Next review date: ${nextReviewDate}
            </div>
            ` : nothing}
          ${owners.length == 1 ? html`
            <div>
              Owner: ${owners[0]}
            </div>
            ` : nothing}
          ${owners.length > 1 ? html`
            <div>
              Owners: ${owners.join(', ')}
            </div>
            ` : nothing}
          ${activeApprovals && activeApprovals.length > 0 ? html`
            <div>
              ${this.renderApprovalsSoFar(activeApprovals)}
            </div>
            ` : nothing}
          ${recentComment ? html`
            <div>
              Comment: ${recentComment.content}
            </div>
            ` : nothing}
        </div>
      `;
    }
    return nothing;
  }

  renderFeature(feature) {
    return html`
      <tr>
        <td class="name_col">
          ${this.renderQuickActions(feature)}
          <a href="/feature/${feature.id}?context=myfeatures">${feature.name}</a>
          ${this.renderHighlights(feature)}
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
