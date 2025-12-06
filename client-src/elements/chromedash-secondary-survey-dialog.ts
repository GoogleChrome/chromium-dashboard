import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {SlRadioGroup, SlTextarea} from '@shoelace-style/shoelace';
import {customElement, property} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';
import {GATE_TYPES} from './form-field-enums.js';

let secondarySurveyDialogEl;

export function isTestingGate(gate: {gate_type: number}): boolean {
  return (
    gate.gate_type === GATE_TYPES.TESTING_PLAN ||
    gate.gate_type === GATE_TYPES.TESTING_SHIP
  );
}

export function shouldShowSecondarySurveyDialog(gate: {
  gate_type: number;
}): boolean {
  return isTestingGate(gate);
}

export async function maybeOpenSecondarySurveyDialog(gate: GateDict) {
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
    secondarySurveyDialogEl = document.createElement(
      'chromedash-secondary-survey-dialog'
    );
    document.body.appendChild(secondarySurveyDialogEl);
  }
  secondarySurveyDialogEl.gate = gate;
  secondarySurveyDialogEl.resolve = resolve;
  await secondarySurveyDialogEl.updateComplete;
  secondarySurveyDialogEl.show();
}

@customElement('chromedash-secondary-survey-dialog')
export class ChromedashSecondaySurveyDialog extends LitElement {
  @property({type: Object})
  gate!: {gate_type: number};
  @property({attribute: false})
  resolve: (commentText?: string) => void = () => {
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

  generateTestingComment() {
    const answer1 =
      this.renderRoot.querySelector<SlRadioGroup>('#coverage')!.value;
    const answer2 =
      this.renderRoot.querySelector<SlTextarea>('#performance_tests')!.value;
    const answer3 =
      this.renderRoot.querySelector<SlRadioGroup>('#automation')!.value;
    const answer4 = this.renderRoot.querySelector<SlTextarea>('#impact')!.value;

    const commentText = `Survey answers:
> 1. Does your feature have sufficient automated
> test coverage (Unit tests, WPT, browser tests
> and other integration tests)?

${answer1}

> 2. How are performance tests conducted on
> Chromium builders?

${answer2}

> 3. Does this feature have non-automatable test
> cases that require manual testing? Do you have
> a plan to get them tested?

${answer3}

> 4. If your feature impacts Google products,
> please fill in  go/chrome-wp-test-survey.

${answer4}
`;

    this.resolve(commentText);
  }

  handleGenerateComment() {
    if (isTestingGate(this.gate)) {
      this.generateTestingComment();
    }
    this.hide();
  }

  renderTestingContent() {
    const option1a =
      'Yes. My feature met the minimum automated test coverage and health requirements.';
    const option1b = 'No. My feature does not meet the requirements.';
    const option3a = 'No. All feature related test cases are automated.';
    const option3b =
      'Yes. There are non-automatable test cases and I have completed test execution or allocated resources to ensure the coverage of these test cases.';
    const option3c =
      'Yes. There are non-automatable test cases and my feature impacts Google products.';

    return html`
      <ol>
        <li>
          <b
            >Does your feature have sufficient automated test coverage (Unit
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
          >? Do the automated tests have more than 93% green (flakiness < 7%) on
          CQ and CI builders?

          <sl-radio-group id="coverage">
            <sl-radio value="${option1a}" size="small"> ${option1a} </sl-radio>
            <sl-radio value="${option1b}" size="small"> ${option1b} </sl-radio>
          </sl-radio-group>
        </li>

        <li>
          <b>How are performance tests conducted on Chromium builders?</b> List
          links to tests if any.

          <sl-textarea id="performance_tests" size="small" rows="2">
          </sl-textarea>
        </li>

        <li>
          <b
            >Does this feature have non-automatable test cases that require
            manual testing? Do you have a plan to get them tested?</b
          >

          <sl-radio-group id="automation">
            <sl-radio value="${option3a}" size="small"> ${option3a} </sl-radio>
            <sl-radio value="${option3b}" size="small"> ${option3b} </sl-radio>
            <sl-radio value="${option3c}" size="small"> ${option3c} </sl-radio>
          </sl-radio-group>
        </li>

        <li>
          <b
            >If your feature impacts Google products, please fill in
            <a href="http://go/chrome-wp-test-survey" target="_blank"
              >go/chrome-wp-test-survey</a
            >.</b
          >
          Make a copy, answer the survey questions, and provide a link to your
          document here.
          <sl-textarea id="impact" size="small" rows="2"> </sl-textarea>
        </li>
      </ol>
    `;
  }

  render() {
    if (this.gate === undefined) {
      return html`Loading gates...`;
    }

    return html` <sl-dialog label="Additional questions">
      ${isTestingGate(this.gate) ? this.renderTestingContent() : nothing}
      <div>
        <sl-button
          id="generate_button"
          size="small"
          variant="primary"
          @click=${this.handleGenerateComment}
          >Generate comment and request review</sl-button
        >
      </div>
    </sl-dialog>`;
  }
}
