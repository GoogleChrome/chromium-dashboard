import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {findProcessStage, showToastMessage} from './utils';
import './chromedash-intent-template';

class ChromedashGuideIntentPreview extends LitElement {
  static get properties() {
    return {
      featureId: {type: Number},
      gateId: {type: Number},
      feature: {type: Object},
      stage: {type: Object},
      gate: {type: Object},
      processStage: {type: Object},
      loading: {type: Boolean},
      displayFeatureUnlistedWarning: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.gateId = 0;
    this.feature = undefined;
    this.stage = {};
    this.gate = {};
    this.processStage = {};
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
        #content h3 {
          margin-bottom: 10px;
        }
        #content h3:before {
          counter-increment: h3;
          content: counter(h3) '.';
          margin-right: 5px;
        }
        .subject {
          font-size: 16px;
          margin-bottom: 10px;
        }
        .alertbox {
          margin: 2em;
          padding: 1em;
          background: var(--warning-background);
          color: var(--warning-color);
        }
        .inline {
          display: inline;
        }
        .right {
          float: right;
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
      window.csClient.getFeatureProcess(this.featureId),
    ])
      .then(([feature, gates, process]) => {
        this.feature = feature;
        // TODO(DanielRyanSmith): only fetch a single gate based on given ID.
        this.gate = gates.gates.find(gate => gate.id === this.gateId);
        this.stage = this.feature.stages.find(
          stage => this.gate.stage_id === stage.id
        );
        this.processStage = findProcessStage(this.stage, process);

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

  render() {
    if (!this.feature) {
      return nothing;
    }
    let alertBox = nothing;
    if (this.displayFeatureUnlistedWarning) {
      alertBox = html` <div class="alertbox">
        Important: This feature is currently unlisted. Please only share feature
        details with people who are collaborating with you on the feature.
      </div>`;
    }

    return html`
      <div id="content">
        <div id="subheader">
          <div>
            <h2>Next steps for the Blink launch process</h2>
          </div>
        </div>
        ${alertBox}
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
            type="submit"
            value="Send to blink-dev directly"
            class="button inline right"
            id="send-email-button"
          />
          <chromedash-intent-template
            .feature=${this.feature}
            .stage=${this.stage}
            .gate=${this.gate}
            .processStage=${this.processStage}
          >
          </chromedash-intent-template>
        </section>
        <section>
          <h3>Obtain LGTMs from 3 API Owners</h3>
          <span class="help">
            You will need three LGTMs from API owners. According to the
            <a href="http://www.chromium.org/blink#launch-process"
              >Blink Launch process</a
            >
            after that, you're free to ship your feature.
          </span>
        </section>
      </div>
    `;
  }
}

customElements.define(
  'chromedash-guide-intent-preview',
  ChromedashGuideIntentPreview
);
