import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils';


class ChromedashGuideIntentPreview extends LitElement {
  static get properties() {
    return {
      featureId: {type: Number},
      gateId: {type: Number},
      displayFeatureUnlistedWarning: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.gateId = 0;
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

        section {
          max-width: 800px;
          flex: 1 0 auto;
          margin-bottom: 15px;

          > div {
            background: $card-background;
            border: $card-border;
            box-shadow: $card-box-shadow;
            padding: 12px;
            margin: 8px 0 16px 0;
          }

          > p {
            color: #444;
          }
        }

        h3 {
          margin-bottom: 10px;
          &:before {
            counter-increment: h3;
            content: counter(h3) ".";
            margin-right: 5px;
          }
        }
      }
      .subject {
        font-size: 16px;
        margin-bottom: 10px;
      }

      .email {
        .help {
          font-style: italic;
          color: #aaa;
        }

        h4 {
          font-weight: 600;
        }
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
    `];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId, this.stageId),
    ]).then(([feature, gates]) => {
      this.feature = feature;
      // TODO(DanielRyanSmith): only fetch a single gate based on given ID.
      this.gate = gates.gates.find(gate => gate.id === this.gateId);

      if (this.feature.name) {
        document.title = `${this.feature.name} - ${this.appTitle}`;
      }
      if (this.feature.unlisted) {
        this.displayFeatureUnlistedWarning = true;
      }
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  render() {
    let alertBox = nothing;
    if (this.displayFeatureUnlistedWarning) {
      alertBox = html`
        <div class="alertbox">
          Important: This feature is currently unlisted.  Please only share
          feature details with people who are collaborating with you on
          the feature.
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
          sending it to spec-mentors@chromium.org.  They can help make sure
          that your intent email is ready for review.</p>
      </section>
      <section>
        <h3 class="inline">Send this text for your "Intent to ..." email</h3>
        <input type="submit" value="Send to blink-dev directly" class="button inline right" id="send-email-button" />
        <!-- TODO(DanielRyanSmith): intent draft goes here -->
      </section>
      <section>
        <h3>Obtain LGTMs from 3 API Owners</h3>
        <span class="help">
          You will need three LGTMs from API owners.
        According to the
        <a href="http://www.chromium.org/blink#launch-process">Blink Launch process</a>
        after that, you're free to ship your feature.
        </span>
      </section>
    </div>
    `;
  }
}


customElements.define('chromedash-guide-intent-preview', ChromedashGuideIntentPreview);
