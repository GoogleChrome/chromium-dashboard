import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

let prereqsDialogEl;
let currentFeatureId;
let currentStageId;


export async function openPrereqsDialog(featureId, stageId) {
  if (!prereqsDialogEl || currentFeatureId !== featureId ||
      currentStageId !== stageId) {
    prereqsDialogEl = document.createElement('chromedash-ot-create-prereqs-dialog');
    prereqsDialogEl.featureId = featureId;
    prereqsDialogEl.stageId = stageId;
    document.body.appendChild(prereqsDialogEl);
    await prereqsDialogEl.updateComplete;
  }
  currentFeatureId = featureId;
  currentStageId = stageId;
  prereqsDialogEl.show();
}


class ChromedashOTCreationPrereqsDialog extends LitElement {
  static get properties() {
    return {
      featureId: {type: Number},
      stageId: {type: Number},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.stageId = 0;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      #prereqs-list li {
        margin-left: 8px;
        margin-bottom: 8px;
        list-style: circle;
      }
      #prereqs-header {
        margin-bottom: 8px;
      }
      #continue-button {
        float: right;
      }
      `,
    ];
  }

  show() {
    this.shadowRoot.querySelector('sl-dialog').show();
  }

  render() {
    return html`
      <sl-dialog label="Origin trial creation prerequisites">
        <div id="prereqs-header">
          <strong>Before submitting a request</strong>, please ensure the following
          prerequisite steps have been completed:
        </div>
        <br>
        <ul id="prereqs-list">
          <li>Your Intent to Experiment has been drafted.</li>
          <li>The required LGTMs have been received.</li>
          <li>
            The trial's UseCounter has landed on
            <a href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom" target="_blank">
              web_feature.mojom
            </a> and is being properly used.
          </li>
          <li>
            A Chromium trial name has landed on
            <a href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5" target="_blank">
              runtime_enabled_features.json5
            </a>
            <strong>that has not been used for any previous trials</strong>.
            No trial names can be reused, even if used for the same feature!
          </li>
          <li>
            For a third-party trial, the feature entry in
            <a href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5" target="_blank">
              runtime_enabled_features.json5
            </a>
            contains the key "origin_trials_allows_third_party: true".
          </li>
          <li>
            For a critical trial, the feature name has been added to the
            <a href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/common/origin_trials/manual_completion_origin_trial_features.cc;l=17" target="_blank">
              kHasExpiryGracePeriod array
            </a>.
          </li>
        </ul>
        <br>
        <p>
          If you haven't already, please review the docs for
          <a href="https://www.chromium.org/blink/origin-trials/running-an-origin-trial/">
            running an origin trial
          </a>.
          If you have any further questions, contact us at origin-trials-discuss@google.com.
        </p>
        <br>
        <sl-button id="continue-button" variant="primary"
          @click=${() => location.assign(`/ot_creation_request/${this.featureId}/${this.stageId}`)}
          size="small"
        >Proceed</sl-button>
      </sl-dialog>`;
  }
}


customElements.define('chromedash-ot-create-prereqs-dialog', ChromedashOTCreationPrereqsDialog);
