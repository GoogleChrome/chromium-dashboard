import {LitElement, css, html, nothing} from 'lit';
import {STATE_NAMES} from './chromedash-approvals-dialog.js';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashFeatureRow extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      columns: {type: String},
      signedIn: {type: Boolean},
      canEdit: {type: Boolean},
      canApprove: {type: Boolean},
      starredFeatures: {type: Object},
      approvals: {type: Object},
      configs: {type: Object},
    };
  }

  constructor() {
    super();
    this.starredFeatures = new Set();
    this.feature = null;
    this.canEdit = false;
    this.canApprove = false;
    this.approvals = {};
    this.configs = {};
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: table-row;
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
      td.icon_col a {
        padding: 2px 4px;
      }
      td.icon_col a:hover {
        text-decoration: none;
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
      }
      sl-icon-button {
        font-size: 1.3rem;
      }
      sl-icon-button::part(base) {
        color: var(--link-color);
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
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = Number(iconEl.dataset.featureId);
    const newStarred = !this.starredFeatures.has(featureId);

    // handled in chromedash-myfeatures-page.js
    this._fireEvent('star-toggle-event', {
      featureId: featureId,
      doStar: newStarred,
    });
  }

  openApprovalsDialog(feature) {
    // handled in chromedash-myfeatures-page.js
    this._fireEvent('open-approvals-event', {
      feature: feature,
    });
  }

  doLGTM(feature) {
    // TODO(jrobbins): Make it pre-select Approved and add comment.
    this.openApprovalsDialog(feature);
  }

  doSnooze(feature) {
    // TODO(jrobbins): Make it pre-set a new next-review-date value.
    this.openApprovalsDialog(feature);
  }

  renderApprovalsIcon(feature) {
    return html`
      <sl-icon-button
        @click="${() => this.openApprovalsDialog(feature)}"
        title="Review approvals"
        library="material" name="approval"></sl-icon-button>
    `;
  }

  renderEditIcon(feature) {
    return html`
      <sl-icon-button href="/guide/edit/${feature.id}"
        title="Edit feature"
        name="pencil-fill"></sl-icon-button>
    `;
  }

  renderStarIcon(feature) {
    return html`
      <sl-icon-button
        @click=${this.toggleStar}
        title="Receive an email notification when there are updates"
        library="material"
        name="${this.starredFeatures.has(Number(feature.id)) ?
                'star' : 'star_border'}"
        data-feature-id="${feature.id}"></sl-icon-button>
    `;
  }

  renderIcons(feature) {
    if (this.signedIn) {
      return html`
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
      //          @click="${() => this.doLGTM(feature)}">
      //    Add LGTM
      //  </button>
      // `;
      // let snoozeButton = html`
      //  <button data-feature-id="${feature.id}"
      //          @click="${() => this.doSnooze(feature)}">
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
          ${this.renderQuickActions(feature)}
        </div>
      `;
    }
    return nothing;
  }

  render() {
    const feature = this.feature;
    return html`
      <td class="icon_col">
        ${this.renderIcons(feature)}
      </td>
      <td class="name_col">
        <a href="/feature/${feature.id}?context=myfeatures">${feature.name}</a>
        ${this.renderHighlights(feature)}
      </td>
    `;
  }
}

customElements.define('chromedash-feature-row', ChromedashFeatureRow);
