import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property, state} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';
import {
  FEATURE_TYPES,
  GATE_PREPARING,
  VOTE_OPTIONS,
  VOTE_NA_SELF,
} from './form-field-enums';

type statusEnum =
  | 'Not started'
  | 'In-progress'
  | 'Needs work'
  | 'Approved'
  | 'Denied';

const STATUS_TO_ICON_NAME: Record<statusEnum, string> = {
  'Not started': 'arrow_circle_right_20px',
  'In-progress': 'pending_20px',
  'Needs work': 'autorenew_20px',
  Approved: 'check_circle_filled_20px',
  Denied: 'block_20px',
};

@customElement('chromedash-review-status-icon')
export class ChromedashReviewStatusIcon extends LitElement {
  @property({type: Object})
  feature!: {id: number; feature_type_int: number; roadmap_stage_ids: number[]};

  @state()
  gates: GateDict[] = [];

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-icon {
          width: 26px;
          height: 18px;
        }

        sl-icon.not-started {
          color: var(--gate-preparing-icon-color);
        }
        sl-icon.in-progress {
          color: var(--gate-pending-icon-color);
        }
        sl-icon.needs-work {
          color: var(--gate-needs-work-icon-color);
        }
        sl-icon.approved {
          color: var(--gate-approved-icon-color);
        }
        sl-icon.denied {
          color: var(--gate-denied-icon-color);
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.gates = [];
    window.csClient?.getGates(this.feature?.id).then(gatesRes => {
      let featureGates = gatesRes.gates;
      this.gates = featureGates.filter(g =>
        this.feature.roadmap_stage_ids?.includes(g.stage_id)
      );
    });
  }

  calcStatus(): {status: statusEnum; targetGateId: number | undefined} {
    let status: statusEnum = 'Not started';
    let targetGateId: number | undefined = undefined;
    let apiOwnersGateId: number | undefined = undefined;

    for (const g of this.gates) {
      // If any gate has started, the review icon moves out of the
      // default 'Not stated'.
      if (g.state !== GATE_PREPARING) {
        status = 'In-progress';
      }
      // If any gate is not approved, let's link to it.
      if (
        g.state !== VOTE_OPTIONS['APPROVED'][0] &&
        g.state !== VOTE_OPTIONS['NA'][0] &&
        g.state !== VOTE_NA_SELF
      ) {
        targetGateId = g.id;
      }
      // Keep track of the API Owners gate because we might link to it below.
      if (g.team_name === 'API Owners') {
        apiOwnersGateId = g.id;
      }
    }

    // If everything was approved, the icon is approved and
    // links to the API Owners gate.
    if (
      this.gates.length > 0 &&
      this.gates.every(
        g =>
          g.state === VOTE_OPTIONS['APPROVED'][0] ||
          g.state === VOTE_OPTIONS['NA'][0] ||
          g.state === VOTE_NA_SELF
      )
    ) {
      status = 'Approved';
      targetGateId = apiOwnersGateId;
    }

    // Assume that PSA features are approved even if not started,
    // since they do not require obtaining approvals.
    // TODO(DanielRyanSmith): This conditional can be removed once PSA
    // shipping stages no longer have API owner gates.
    if (
      this.feature?.feature_type_int ===
      FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]
    ) {
      status = 'Approved';
      targetGateId = undefined;
    }

    // If any gate needs work, the icon needs work and links to that gate.
    for (const g of this.gates) {
      if (g.state == VOTE_OPTIONS['NEEDS_WORK'][0]) {
        status = 'Needs work';
        targetGateId = g.id;
      }
    }
    // If any gate is denied, the icon is denied and links to that gate.
    for (const g of this.gates) {
      if (g.state == VOTE_OPTIONS['DENIED'][0]) {
        status = 'Denied';
        targetGateId = g.id;
      }
    }

    return {status, targetGateId};
  }

  render() {
    if (this.gates.length === 0) {
      return html`<sl-icon></sl-icon>`;
    }

    const {status, targetGateId} = this.calcStatus();
    let className = status.toLowerCase().replace(' ', '-');
    let iconName = STATUS_TO_ICON_NAME[status];
    let hoverText = 'Reviews: ' + status;
    const icon = html`
      <sl-icon
        library="material"
        title="${hoverText}"
        class="${className}"
        name="${iconName}"
      ></sl-icon>
    `;

    if (targetGateId) {
      return html`
        <a href="/feature/${this.feature.id}?gate=${targetGateId}">${icon}</a>
      `;
    } else {
      return icon;
    }
  }
}
