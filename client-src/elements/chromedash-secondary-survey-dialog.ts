import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';
import {GATE_TYPES} from './form-field-enums.js';

let secondarySurveyDialogEl;

function isTestingGate(gate: GateDict): boolean {
  return (
    gate.gate_type === GATE_TYPES.TESTING_PLAN ||
    gate.gate_type === GATE_TYPES.TESTING_SHIP);
}

function shouldShowSecondarySurveyDialog(gate: GateDict): boolean {
  return isTestingGate(gate);
}

export async function maybeOpenSecondarySurveyDialog(
  gate: GateDict,
) {
  if (shouldShowSecondarySurveyDialog(gate)) {
    return new Promise(resolve => {
      openSecondarySurveyDialog(gate, resolve);
    });
  } else {
    return Promise.resolve();
  }
}

async function openSecondarySurveyDialog(gate, resolve) {
  if (!secondarySurveyDialogEl) {
    secondarySurveyDialogEl = document.createElement('chromedash-secondary-survey-dialog');
    document.body.appendChild(secondarySurveyDialogEl);
  }
  secondarySurveyDialogEl.gate = gate;
  secondarySurveyDialogEl.resolve = resolve;
  await secondarySurveyDialogEl.updateComplete;
  secondarySurveyDialogEl.show();
}


@customElement('chromedash-secondary-survey-dialog')
class ChromedashSelfCertifyDialog extends LitElement {
  @property({type: Object})
  gate!: GateDict;
  @property({attribute: false})
  resolve: () => void = () => {
    console.log('Missing resolve action');
  };

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      ol {
      padding-left: var(--content-padding-half);
      }

        ol li {
      margin-bottom: var(--content-padding);
        }
        sl-button {
          float: right;
          margin: var(--content-padding-half);
        }
      `,
    ];
  }

  show() {
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleGenerateComment() {
    // actually post the comment
    this.resolve();
    this.hide();
  }

  renderTestingContent() {
    return html`
    <ol>
    <li><b>Does your feature have sufficient automated test coverage (Unit
      tests, WPT, browser tests and other integration tests)?</b
    >
    Chrome requires at least 70% automation code coverage (<a
      href="https://analysis.chromium.org/coverage/p/chromium"
      target="_blank"
      >dashboard</a
    >) running on the main/release branch and 70% Changelist
    <a
      href="https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/testing/code_coverage_in_gerrit.md"
      target="_blank"
      >code coverage in Gerrit</a
    >? Do the automated tests have more than 93% green (flakiness < 7%) on CQ
    and CI builders?

    <sl-radio-group id="coverage">
      <sl-radio value="yes" size=small>
        Yes. My feature met the minimum automated test coverage and health
        requirements.
      </sl-radio>
      <sl-radio value="no" size=small>
       No. My feature does not meet the requirements.
      </sl-radio>
    </sl-radio-group>
    </li>

    <li><b>How are performance tests conducted on Chromium builders?</b> List
    links to tests if any.

    <sl-textarea id="performance_tests" size=small rows=2>
    </sl-textarea>
    </li>

    <li><b>Does this feature have non-automatable test cases that require manual
      testing? Do you have a plan to get them tested?</b>

    <sl-radio-group id="coverage">
    <sl-radio value="no" size=small>
    No. All feature related test cases are automated.
      </sl-radio>
    <sl-radio value="yes_completed" size=small>
    Yes. There are non-automatable test cases and I have completed test
      execution or allocated resources to ensure the coverage of these test
      cases.
      </sl-radio>
    <sl-radio value="yes_google" size=small>
    Yes. There are non-automatable test cases and my feature impacts Google
      products.
      </sl-radio>
    </sl-radio-group>
    </li>

    <li>
    <b
      >(4) If your feature impacts Google products, please fill in
      <a href="http://go/chrome-wp-test-survey" target="_blank"
        >go/chrome-wp-test-survey</a
      >.</b
    >
    Make a copy, answer the survey questions, and provide a link to your
    document here.
    <sl-textarea id="impact" size=small rows=2>
    </sl-textarea>
    </li>

    </ol>

      <div>
      <sl-button size="small" variant="primary" @click=${this.handleGenerateComment}
        >Generate comment and request review</sl-button
      ></div>
    `;
  }


  render() {
    if (this.gate === undefined) {
      return html`Loading gates...`;
    }

    return html` <sl-dialog label="Additional questions">
      ${isTestingGate(this.gate) ? this.renderTestingContent() : nothing}
    </sl-dialog>`;
  }
}
