import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils.js';
import {customElement, property} from 'lit/decorators.js';
import {StageDict} from '../js-src/cs-client.js';

let dialogEl;
let currentFeatureId;
let currentStageId;

export const dialogTypes = {
  CREATION: 1,
  EXTENSION: 2,
  END_MILESTONE_EXPLANATION: 3,
  FINALIZE_EXTENSION: 4,
};

export async function openPrereqsDialog(featureId, stage, dialogType) {
  if (
    !dialogEl ||
    currentFeatureId !== featureId ||
    currentStageId !== stage.id
  ) {
    dialogEl = document.createElement('chromedash-ot-prereqs-dialog');
    dialogEl.featureId = featureId;
    dialogEl.stage = stage;
    dialogEl.dialogType = dialogType;
    document.body.appendChild(dialogEl);
    await dialogEl.updateComplete;
  }
  currentFeatureId = featureId;
  currentStageId = stage.id;
  dialogEl.show();
}

export async function openInfoDialog(dialogType) {
  if (!dialogEl) {
    dialogEl = document.createElement('chromedash-ot-prereqs-dialog');
    dialogEl.dialogType = dialogType;
    document.body.appendChild(dialogEl);
    await dialogEl.updateComplete;
  }
  dialogEl.show();
}

export async function openFinalizeExtensionDialog(
  featureId,
  stage,
  milestone,
  dialogType
) {
  if (
    !dialogEl ||
    currentFeatureId !== featureId ||
    currentStageId !== stage.id
  ) {
    dialogEl = document.createElement('chromedash-ot-prereqs-dialog');
    dialogEl.featureId = featureId;
    dialogEl.stage = stage;
    dialogEl.dialogType = dialogType;
    dialogEl.milestone = milestone;
    document.body.appendChild(dialogEl);
    await dialogEl.updateComplete;
  }
  dialogEl.dialogType = dialogType;
  currentFeatureId = featureId;
  currentStageId = stage.id;
  dialogEl.show();
}

@customElement('chromedash-ot-prereqs-dialog')
class ChromedashOTPrereqsDialog extends LitElement {
  @property({type: Number})
  featureId = 0;
  @property({attribute: false})
  stage!: StageDict;
  @property({type: Number})
  milestone = 0;
  @property({type: Number})
  dialogType = 0;

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
        #update-button {
          margin-right: 8px;
        }
        .float-right {
          float: right;
        }
      `,
    ];
  }

  show() {
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  renderEndMilestoneExplanationDialog() {
    return html` <sl-dialog label="End milestone date">
      <p>
        When a specific milestone is approved by API owners, the trial's end
        date is set based on the stable release date of (end milestone +2). Most
        of the time when a trial ends, the feature will be enabled by default
        within the next Chrome release. This additional trial time window
        ensures users don't see breakage before upgrading to the version with
        the feature enabled by default.
      </p>
    </sl-dialog>`;
  }

  submitTrialExtension() {
    window.csClient
      .extendOriginTrial(this.featureId, this.stage.id)
      .then(() => {
        showToastMessage('Extension processed!');
        setTimeout(() => {
          location.assign(`/feature/${this.featureId}`);
        }, 1000);
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  renderThreadMissingDialog() {
    return html`<sl-dialog label="Intent thread not found">
      <p>
        LGTMs have been detected for this trial extension, but
        <strong>no intent thread link has been detected or provided</strong>.
        All extension proposals must be discussed publicly on blink-dev. Please
        add the value to the "Intent to Extend Experiment link" field by
        selecting "Edit fields" button on your feature's "Origin Trial" section.
      </p>
    </sl-dialog>`;
  }

  renderFinalizeExtensionDialog() {
    if (!this.stage.intent_thread_url) {
      return this.renderThreadMissingDialog();
    }
    return html` <sl-dialog label="Finalize trial extension">
      <p>
        LGTMs have been detected for this trial extension. This origin trial
        will be extended <strong>through milestone ${this.milestone}</strong>.
        Is this correct?
      </p>
      <br />
      <sl-button
        class="float-right"
        variant="primary"
        size="small"
        @click=${() => this.submitTrialExtension()}
        >Proceed</sl-button
      >
      <sl-button
        class="float-right"
        id="update-button"
        variant="info"
        size="small"
        @click=${() =>
          location.assign(
            `/guide/stage/${this.featureId}/${this.stage.id}?updateExtension`
          )}
        >Change milestone</sl-button
      >
    </sl-dialog>`;
  }

  renderExtensionPrereqs() {
    return html` <sl-dialog label="Origin trial extension prerequisites">
      <div id="prereqs-header">
        <strong>Before submitting an extension request</strong>, please ensure
        that your Intent to Extend Experiment has been drafted, and the required
        LGTMs have been received.
        <br />
        <a
          target="_blank"
          href="https://www.chromium.org/blink/origin-trials/running-an-origin-trial/#what-is-the-process-to-extend-an-origin-trial"
        >
          View documentation on the trial extension process
        </a>
      </div>
      <br />
      <sl-button
        id="continue-button"
        variant="primary"
        @click=${() =>
          location.assign(
            `/ot_extension_request/${this.featureId}/${this.stage.id}`
          )}
        size="small"
        >Proceed</sl-button
      >
    </sl-dialog>`;
  }

  renderCreationPrereqs() {
    return html` <sl-dialog label="Origin trial creation prerequisites">
      <div id="prereqs-header">
        <strong>Before submitting a creation request</strong>, please ensure the
        following prerequisite steps have been completed:
      </div>
      <br />
      <ul id="prereqs-list">
        <li>
          The trial's UseCounter has landed on
          <a
            href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom"
            target="_blank"
          >
            web_feature.mojom
          </a>
          and is being properly used.
        </li>
        <li>
          A Chromium trial name has landed on
          <a
            href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5"
            target="_blank"
          >
            runtime_enabled_features.json5
          </a>
          <strong>that has not been used for any previous trials</strong>. No
          trial names can be reused, even if used for the same feature!
        </li>
        <li>
          For a third-party trial, the feature entry in
          <a
            href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5"
            target="_blank"
          >
            runtime_enabled_features.json5
          </a>
          contains the key "origin_trials_allows_third_party: true".
        </li>
        <li>
          For a critical trial, the feature name has been added to the
          <a
            href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/common/origin_trials/manual_completion_origin_trial_features.cc;l=17"
            target="_blank"
          >
            kHasExpiryGracePeriod array </a
          >.
        </li>
      </ul>
      <br />
      <p>
        If you haven't already, please review the docs for
        <a
          href="https://www.chromium.org/blink/origin-trials/running-an-origin-trial/"
        >
          running an origin trial </a
        >. If you have any further questions, contact us at
        origin-trials-support@google.com.
      </p>
      <br />
      <sl-button
        class="float-right"
        variant="primary"
        @click=${() =>
          location.assign(
            `/ot_creation_request/${this.featureId}/${this.stage.id}`
          )}
        size="small"
        >Proceed</sl-button
      >
    </sl-dialog>`;
  }

  render() {
    if (this.dialogType === dialogTypes.END_MILESTONE_EXPLANATION) {
      return this.renderEndMilestoneExplanationDialog();
    }
    if (this.dialogType === dialogTypes.FINALIZE_EXTENSION) {
      return this.renderFinalizeExtensionDialog();
    }
    if (this.dialogType === dialogTypes.EXTENSION) {
      return this.renderExtensionPrereqs();
    }
    return this.renderCreationPrereqs();
  }
}
