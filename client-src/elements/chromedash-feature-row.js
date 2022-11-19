import {LitElement, css, html, nothing} from 'lit';
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
      gates: {type: Object},
    };
  }

  constructor() {
    super();
    this.starredFeatures = new Set();
    this.feature = null;
    this.canEdit = false;
    this.canApprove = false;
    this.approvals = {};
    this.gates = {};
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

      return html`
        <span class="quick_actions">
          ${threadLinks}
        </span>
      `;
    }
    return nothing;
  }

  isActiveGate(gate) {
    return gate.state == 2 || gate.state == 3 || gate.state == 4;
  }

  getActiveStages(feature) {
    const featureGates = this.gates[feature.id] || [];
    const activeGates = featureGates.filter(g => this.isActiveGate(g));
    const activeStageIds = new Set(activeGates.map(g => g.stage_id));
    const activeStagesAndTheirGates = [];
    for (const activeStageId of activeStageIds) {
      activeStagesAndTheirGates.push({
        stageId: activeStageId,
        gates: featureGates.filter(g => g.stage_id == activeStageId),
      });
    }
    return activeStagesAndTheirGates;
  }

  renderActiveStageAndGates(stageAndGates) {
    const stageName = ''; // TODO(jrobbins) get this data.
    return html`
      <div>
        ${stageName}
        ${stageAndGates.gates.map(gate => html`
          <chromedash-gate-chip
            .feature=${this.feature}
            .gate=${gate}
          ></chromedash-gate-chip>`)}
      </div>
    `;
  }

  renderHighlights(feature) {
    if (this.columns == 'approvals') {
      const activeStages = this.getActiveStages(feature);
      // TODO(jrobbins): group gates by stage

      return html`
        <div class="highlights">
          ${activeStages.length > 0 ? html`
            <div>
              ${activeStages.map(stageAndGates =>
                this.renderActiveStageAndGates(stageAndGates))}
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
      <td class="name_col">
        <a href="/feature/${feature.id}?context=myfeatures">${feature.name}</a>
        ${this.renderHighlights(feature)}
      </td>
      <td class="icon_col">
        ${this.renderIcons(feature)}
      </td>
    `;
  }
}

customElements.define('chromedash-feature-row', ChromedashFeatureRow);
