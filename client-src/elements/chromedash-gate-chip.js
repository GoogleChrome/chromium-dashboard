import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';


const GATE_STATE_TO_NAME = {
  // TODO(jrobbins): NOT_STARTED.
  1: 'FYI', //  NA
  2: 'Pending', // REVIEW_REQUESTED
  3: 'Pending', // REVIEW_STARTED
  4: 'Needs work', // NEEDS_WORK
  5: 'Approved', // APPROVED
  6: 'Denied', // DENIED
  // TODO(jrobbins): COMPLETE for auto-approved.
};

const GATE_STATE_TO_ICON = {
  // TODO(jrobbins): arrow_circle_right_20px NOT_STARTED.
  1: 'visibility_20px', //  NA
  2: 'pending_20px', // REVIEW_REQUESTED
  3: 'pending_20px', // REVIEW_STARTED
  4: 'autorenew_20px', // NEEDS_WORK
  5: 'check_circle_filled_20px', // APPROVED
  6: 'block_20px', // DENIED
  // TODO(jrobbins): COMPLETE for auto-approved also check_circle_filled_20px.
};


class ChromedashGateChip extends LitElement {
  static get properties() {
    return {
      gate: {type: Object},
    };
  }

  constructor() {
    super();
    this.gate = {};
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      sl-icon {
        font-size: 1.3rem;
      }

     sl-button::part(base) {
       border: var(--chip-border);
       padding: 0 0 0 5px;
       height: 27px;
     }

     sl-button.fyi::part(base) {
       background: var(--gate-fyi-background);
       color: var(--gate-fyi-color);
     }
     .fyi sl-icon {
       color: var(--gate-fyi-icon-color);
     }

     sl-button.pending::part(base) {
       background: var(--gate-pending-background);
       color: var(--gate-pending-color);
     }
     .pending sl-icon {
       color: var(--gate-pending-icon-color);
     }

     sl-button.needs_work::part(base) {
       background: var(--gate-needs-work-background);
       color: var(--gate-needs-work-color);
     }
     .needs_work sl-icon {
       color: var(--gate-needs-work-icon-color);
     }

     sl-button.approved::part(base) {
       background: var(--gate-approved-background);
       color: var(--gate-approved-color);
     }
     .approved sl-icon {
       color: var(--gate-approved-icon-color);
     }

     sl-button.denied::part(base) {
       background: var(--gate-denied-background);
       color: var(--gate-denied-color);
     }
     .denied sl-icon {
       color: var(--gate-denied-icon-color);
     }
    `];
  }

  render() {
    if (this.gate === undefined || this.gate == {}) {
      return nothing;
    }
    const teamName = this.gate.team_name;
    const gateName = this.gate.name;
    const stateName = GATE_STATE_TO_NAME[this.gate.state];
    const className = stateName.toLowerCase().replaceAll(' ', '_');
    const iconName = GATE_STATE_TO_ICON[this.gate.state];

    return html`
      <sl-button pill size="small" class=${className}
        title="${teamName}: ${gateName}: ${stateName}">
        <sl-icon slot="prefix" library="material" name=${iconName}></sl-icon>
        ${teamName}
      </sl-button>
    `;
  }
}

customElements.define('chromedash-gate-chip', ChromedashGateChip);
