import {LitElement, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {
  GATE_ACTIVE_REVIEW_STATES,
  GATE_TEAM_ORDER,
  STAGE_SHORT_NAMES,
} from './form-field-enums';
import {GateDict} from './chromedash-gate-chip.js';

interface ActiveStagesAndGates {
  stage: StageDict;
  gates: GateDict[]; // TODO(markxiong0122): Add Gate type when PR#4060 is merged.
}

@customElement('chromedash-feature-row')
class ChromedashFeatureRow extends LitElement {
  @property({attribute: false})
  feature!: Feature;
  @property({type: String})
  columns: undefined | 'approvals' = undefined;
  @property({type: Boolean})
  canEdit = false;
  @property({type: Boolean})
  signedIn = false;
  @property({attribute: false})
  starredFeatures = new Set<number>();
  @property({attribute: false})
  gates: Record<number, GateDict[]> = {};
  @property({type: Number})
  selectedGateId = 0;

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
      `,
    ];
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

  renderStarIcon(feature) {
    return html`
      <sl-icon-button
        @click=${this.toggleStar}
        title="Receive an email notification when there are updates"
        library="material"
        name="${this.starredFeatures.has(Number(feature.id))
          ? 'star'
          : 'star_border'}"
        data-feature-id="${feature.id}"
      ></sl-icon-button>
    `;
  }

  renderIcons(feature) {
    if (this.signedIn) {
      return html` ${this.renderStarIcon(feature)} `;
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

      return html` <span class="quick_actions"> ${threadLinks} </span> `;
    }
    return nothing;
  }

  isActiveGate(gate) {
    return GATE_ACTIVE_REVIEW_STATES.includes(gate.state);
  }

  getActiveStages(feature) {
    const featureGates: GateDict[] = this.gates[feature.id] || [];
    const activeGates = featureGates.filter(g => this.isActiveGate(g));
    const activeStageIds = new Set(activeGates.map(g => g.stage_id));
    const activeStagesAndTheirGates: ActiveStagesAndGates[] = [];
    for (const stage of feature.stages) {
      if (activeStageIds.has(stage.id)) {
        activeStagesAndTheirGates.push({
          stage: stage,
          gates: featureGates.filter(g => g.stage_id == stage.id),
        });
      }
      for (const extension of stage.extensions || []) {
        if (activeStageIds.has(extension.id)) {
          activeStagesAndTheirGates.push({
            stage: extension,
            gates: featureGates.filter(g => g.stage_id == extension.id),
          });
        }
      }
    }
    return activeStagesAndTheirGates;
  }

  getStageShortName(stage) {
    if (STAGE_SHORT_NAMES[stage.stage_type]) {
      return `${STAGE_SHORT_NAMES[stage.stage_type]}: `;
    } else {
      return nothing;
    }
  }

  renderActiveStageAndGates(stageAndGates) {
    const sortedGates = stageAndGates.gates;
    sortedGates.sort(
      (g1, g2) =>
        GATE_TEAM_ORDER.indexOf(g1.team_name) -
        GATE_TEAM_ORDER.indexOf(g2.team_name)
    );
    return html`
      <div>
        ${this.getStageShortName(stageAndGates.stage)}
        ${sortedGates.map(
          gate => html`
            <chromedash-gate-chip
              .feature=${this.feature}
              .stage=${stageAndGates.stage}
              .gate=${gate}
              selectedGateId=${this.selectedGateId}
            ></chromedash-gate-chip>
          `
        )}
      </div>
    `;
  }

  renderHighlights(feature) {
    if (this.columns == 'approvals') {
      const activeStages = this.getActiveStages(feature);

      return html`
        <div class="highlights">
          ${activeStages.length > 0
            ? html`
                <div>
                  ${activeStages.map(stageAndGates =>
                    this.renderActiveStageAndGates(stageAndGates)
                  )}
                </div>
              `
            : nothing}
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
        <a href="/feature/${feature.id}">${feature.name}</a>
        ${this.renderHighlights(feature)}
      </td>
      <td class="icon_col">${this.renderIcons(feature)}</td>
    `;
  }
}
