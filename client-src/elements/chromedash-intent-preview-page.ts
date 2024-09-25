import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils.js';
import {openPostIntentDialog} from './chromedash-post-intent-dialog.js';
import {
  STAGE_TYPES_DEV_TRIAL,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums.js';
import './chromedash-intent-content.js';
import {customElement, property, state} from 'lit/decorators.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';

@customElement('chromedash-intent-preview-page')
class ChromedashIntentPreviewPage extends LitElement {
  @property({type: String})
  appTitle = '';
  @property({type: Number})
  featureId = 0;
  @property({type: Number})
  gateId = 0;
  @state()
  feature!: Feature;
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;
  @state()
  loading = false;
  @state()
  subject = '';
  @state()
  intentBody = '';
  @state()
  displayFeatureUnlistedWarning = false;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #content {
          flex-direction: column;
          counter-reset: h3;
          height: auto;
        }
        #content section {
          max-width: 800px;
          flex: 1 0 auto;
          margin-bottom: 15px;
        }
        h3 {
          margin-bottom: 10px;
        }
        #content h3:before {
          counter-increment: h3;
          content: counter(h3) '.';
          margin-right: 5px;
        }
        #post-intent-button {
          float: right;
        }
        .inline {
          display: inline;
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId),
    ])
      .then(([feature, gates]) => {
        this.feature = feature;
        document.title = `${this.feature.name} - ${this.appTitle}`;
        // TODO(DanielRyanSmith): only fetch a single gate based on given ID.
        if (this.gateId) {
          this.gate = gates.gates.find(gate => gate.id === this.gateId);
        }
        if (this.gate) {
          // Find the stage that matches the given gate.
          for (const stage of this.feature.stages) {
            if (this.stage) {
              break;
            }
            if (stage.id === this.gate.stage_id) {
              this.stage = stage;
            }
            // Check if gate matches an extension stage.
            if (!this.stage) {
              const extensionStage = stage.extensions.find(
                e => e.id === this.gate.stage_id
              );
              if (extensionStage) {
                this.stage = extensionStage;
              }
            }
          }
        } else if (!this.gateId) {
          // This is a "Ready for Developer Testing" intent if no gate is supplied (0).
          const devTrialStage = this.feature.stages.find(stage =>
            STAGE_TYPES_DEV_TRIAL.has(stage.stage_type)
          );
          if (devTrialStage) {
            this.stage = devTrialStage;
          }
        } else {
          throw new Error('Invalid gate ID');
        }

        if (this.feature.unlisted) {
          this.displayFeatureUnlistedWarning = true;
        }
        // Finally, get the contents of the intent based on the feature/stage.
        return window.csClient.getIntentBody(
          this.featureId,
          this.stage.id,
          this.gateId
        );
      })
      .then(intentResp => {
        this.subject = intentResp.subject;
        this.intentBody = intentResp.email_body;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  renderThreeLGTMSection() {
    // Show for shipping stages only.
    if (!STAGE_TYPES_SHIPPING.has(this.stage?.stage_type)) return nothing;
    return html` <section>
      <h3>Obtain LGTMs from 3 API Owners</h3>
      <span class="help">
        You will need three LGTMs from API owners. According to the
        <a href="http://www.chromium.org/blink#launch-process"
          >Blink Launch process</a
        >
        after that, you're free to ship your feature.
      </span>
    </section>`;
  }

  renderFeatureUnlistedAlert() {
    if (!this.displayFeatureUnlistedWarning) return nothing;
    return html`<div class="alertbox">
      Important: This feature is currently unlisted. Please only share feature
      details with people who are collaborating with you on the feature.
    </div>`;
  }

  renderSkeletonSection() {
    return html`
      <section>
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  renderSkeletons() {
    return html`
      <div id="feature" style="margin-top: 65px;">
        ${this.renderSkeletonSection()} ${this.renderSkeletonSection()}
        ${this.renderSkeletonSection()} ${this.renderSkeletonSection()}
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return this.renderSkeletons();
    }
    return html`
      <div id="content">
        <div id="subheader">
          <div>
            <h2>Next steps for the Blink launch process</h2>
          </div>
        </div>
        ${this.renderFeatureUnlistedAlert()}
        <section>
          <h3>Reach out to a spec mentor</h3>
          <p style="margin-left: 1em">
            Consider showing your draft intent email to your spec mentor or
            sending it to spec-mentors@chromium.org. They can help make sure
            that your intent email is ready for review.
          </p>
        </section>
        <section>
          <h3 class="inline">Send this text for your "Intent to ..." email</h3>
          <input
            ref()
            id="post-intent-button"
            class="button inline"
            type="submit"
            value="Post directly to blink-dev"
            @click="${() =>
              openPostIntentDialog(
                this.feature.id,
                this.stage.id,
                this.feature.owner_emails,
                this.gate?.id
              )}"
          />
          <chromedash-intent-content
            appTitle="${this.appTitle}"
            .feature=${this.feature}
            .stage=${this.stage}
            subject="${this.subject}"
            intentBody="${this.intentBody}"
          >
          </chromedash-intent-content>
        </section>
        ${this.renderThreeLGTMSection()}
      </div>
    `;
  }
}
