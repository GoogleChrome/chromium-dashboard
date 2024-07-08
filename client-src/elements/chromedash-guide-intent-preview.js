import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils';
import {openPostIntentDialog} from './chromedash-post-intent-dialog.js'
import {STAGE_TYPES_SHIPPING} from './form-field-enums.js';
import './chromedash-intent-template';

class ChromedashGuideIntentPreview extends LitElement {
  static get properties() {
    return {
      appTitle: {type: String},
      featureId: {type: Number},
      gateId: {type: Number},
      feature: {type: Object},
      stage: {type: Object},
      gate: {type: Object},
      loading: {type: Boolean},
      displayFeatureUnlistedWarning: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.appTitle = '';
    this.featureId = 0;
    this.gateId = 0;
    this.feature = undefined;
    this.stage = undefined;
    this.gate = undefined;
    this.loading = true;
    this.displayFeatureUnlistedWarning = false;
  }

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
        // TODO(DanielRyanSmith): only fetch a single gate based on given ID.
        if (this.gateId) {
          this.gate = gates.gates.find(gate => gate.id === this.gateId);
        }
        if (this.gate) {
          this.stage = this.feature.stages.find(
            stage => this.gate.stage_id === stage.id
          );
        }

        if (this.feature.name) {
          document.title = `${this.feature.name} - ${this.appTitle}`;
        }
        if (this.feature.unlisted) {
          this.displayFeatureUnlistedWarning = true;
        }
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

  render() {
    if (!this.feature) return nothing;

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
            id="submit-button"
            class="button inline"
            type="submit"
            value="Post directly to blink-dev"
            @click="${() => openPostIntentDialog()}"
          />
          <chromedash-intent-template
            appTitle="${this.appTitle}"
            .feature=${this.feature}
            .stage=${this.stage}
            .gate=${this.gate}
          >
          </chromedash-intent-template>
        </section>
        ${this.renderThreeLGTMSection()}
      </div>
    `;
  }
}

customElements.define(
  'chromedash-guide-intent-preview',
  ChromedashGuideIntentPreview
);
