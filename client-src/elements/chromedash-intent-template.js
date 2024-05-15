import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  GATE_TYPES,
  FEATURE_TYPES,
  INTENT_STAGES,
  STAGE_TYPES_INTENT_EXPERIMENT,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_SHIPPING,
  OT_EXTENSION_STAGE_TYPES,
} from './form-field-enums.js';

class ChromedashIntentTemplate extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      stage: {type: Object},
      gate: {type: Object},
      processStage: {type: Object},
      displayFeatureUnlistedWarning: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.stage = {};
    this.gate = {};
    this.processStage = {};
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .email-content-div {
          background: white;
          border: 1px solid #ddd;
          box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
          padding: 12px;
          margin: 8px 0 16px 0;
        }

        p {
          color: #444;
        }

        h3 {
          margin-bottom: 10px;
          &:before {
            counter-increment: h3;
            content: counter(h3) '.';
            margin-right: 5px;
          }
        }
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
        #content section > div {
          background: white;
          border: 1px solid #ddd;
          box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
          padding: 12px;
          margin: 8px 0 16px 0;
        }
        #content section > p {
          color: #444;
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

        .email .help {
          font-style: italic;
          color: #aaa;
        }
        .email h4 {
          font-weight: 600;
        }

        .alertbox {
          margin: 2em;
          padding: 1em;
          background: var(--warning-background);
          color: var(--warning-color);
        }
      `,
    ];
  }

  computeSubjectPrefix() {
    if (this.gate.gate_type === GATE_TYPES.API_PROTOTYPE) {
      if (
        this.feature.feature_type_int ===
        FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID
      ) {
        return 'Intent to Deprecate and Remove';
      }
      return 'Intent to Prototype';
    }
    if (this.gate.gate_type === GATE_TYPES.API_ORIGIN_TRIAL) {
      if (
        this.feature.feature_type_int ===
        FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID
      ) {
        return 'Request for Deprecation Trial';
      }
      return 'Intent to Experiment';
    }
    if (this.gate.gate_type === GATE_TYPES.API_EXTEND_ORIGIN_TRIAL) {
      if (
        this.feature.feature_type_int ===
        FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID
      ) {
        return 'Intent to Extend Deprecation Trial';
      }
      return 'Intent to Extend Experiment';
    }
    if (this.gate.gate_type === GATE_TYPES.API_SHIP) {
      if (
        this.feature.feature_type_int ===
        FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID
      ) {
        return 'Web-Facing Change PSA';
      }
      return 'Intent to Ship';
    }
    return `Intent stage "${INTENT_STAGES[this.feature.intent_stage]}"`;
  }

  renderOwners() {
    const owners = this.feature.owner_emails;
    let ownersHTML = html`None`;
    if (owners) {
      ownersHTML = owners.map((o, i) => {
        if (i + 1 === owners.length) {
          return html`<a href="mailto:${o}">${o}</a>`;
        }
        return html`<a href="mailto:${o}">${o}</a>,`;
      });
    }
    return html`
      <h4>Contact emails</h4>
      ${ownersHTML}
    `;
  }

  renderExplainerLinks() {
    const explainerLinks = this.feature.explainer_links;
    if (this.feature.feature_type_int === 2) {
      return nothing;
    }

    let explainerLinksHTML = html`None`;
    if (explainerLinks && explainerLinks.length > 0) {
      explainerLinksHTML = explainerLinks.map((link, i) => {
        if (i === 0) {
          return html`<a href="${link}">${link}</a>`;
        }
        return html`<br /><a href="${link}">${link}</a>`;
      });
    }
    return html`
      <br /><br />
      <h4>Explainer</h4>
      ${explainerLinksHTML}
    `;
  }

  renderSpecification() {
    const spec = this.feature.standards?.spec;
    let specHTML = html`None`;
    if (spec) {
      specHTML = html`<a href="${spec}">${spec}</a>`;
    }
    return html`
      <br /><br />
      <h4>Specification</h4>
      ${specHTML}
    `;
  }

  renderDesignDocs() {
    const docs = this.feature.resources?.docs;
    if (!docs || docs.length === 0) return nothing;

    let docsHTML = html`None`;
    docsHTML = docs.map((link, i) => {
      if (i === 0) {
        return html`<a href="${link}">${link}</a>`;
      }
      return html`<br /><a href="${link}">${link}</a>`;
    });
    return html`
      <br /><br />
      <h4>Design docs</h4>
      ${docsHTML}
    `;
  }

  renderSummary() {
    const summary = this.feature.summary;
    let summaryHTML = html`None`;
    if (summary) {
      summaryHTML = html`<p class="preformatted">${this.feature.summary}</p>`;
    }
    return html`
      <br /><br />
      <h4>Summary</h4>
      ${summaryHTML}
    `;
  }

  renderBlinkComponents() {
    const blinkComponents = this.feature.blink_components;
    let blinkComponentsHTML = html`None`;
    if (blinkComponents && blinkComponents.length > 0) {
      blinkComponentsHTML = blinkComponents.map(
        bc =>
          html` <a
            href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${bc}"
            target="_blank"
            rel="noopener"
            >${bc}</a
          >`
      );
    }
    return html`
      <br /><br />
      <h4>Blink Components</h4>
      ${blinkComponentsHTML}
    `;
  }

  renderMotivation() {
    const motivation = this.feature.motivation;
    if (!motivation) return nothing;

    return html`
      <br /><br />
      <h4>Motivation</h4>
      <p class="preformatted">${motivation}</p>
    `;
  }

  renderInitialPublicProposal() {
    const initialPublicProposalUrl = this.feature.initial_public_proposal_url;
    if (!initialPublicProposalUrl) return nothing;

    return html`
      <br /><br />
      <h4>Initial public proposal</h4>
      <a href="${initialPublicProposalUrl}">${initialPublicProposalUrl}</a>
    `;
  }

  renderTags() {
    const tags = this.feature.tags;
    if (!tags || tags.length === 0) return nothing;

    const tagsHTML = tags.map((t, i) => {
      if (i + 1 === tags.length) {
        return html`<a href="/features#tags:${t}">${t}</a>`;
      }
      return html`<a href="/features#tags:${t}">${t}</a>,`;
    });
    return html`
      <br /><br />
      <h4>Search Tags</h4>
      ${tagsHTML}
    `;
  }

  renderTagReview() {
    const tagReview = this.feature.tag_review_status;
    if (!tagReview) return nothing;
    return html` <br /><br />
      <h4>TAG review status</h4>
      ${tagReview}`;
  }

  renderOTInfo() {
    const otStages = this.feature.stages.filter(
      s => s.stage_type in STAGE_TYPES_ORIGIN_TRIAL
    );
    if (otStages.length === 0) return nothing;
    parts = [];
    return otStages.forEach((s, i) => {
      const stageParts = [];
      if (s.ot_chromium_trial_name) {
        stageParts.push(
          html` <br /><br />
            <h4>Chromium Trial Name</h4>
            ${s.ot_chromium_trial_name}`
        );
      }
      if (s.origin_trial_feedback_url) {
        stageParts.push(
          html` <br /><br />
            <h4>Link to origin trial feedback summary</h4>
            ${s.ot_chromium_trial_name}`
        );
      }
      if (s.ot_is_deprecation_trial && s.ot_webfeature_use_counter) {
        stageParts.push(
          html` <br /><br />
            <h4>WebFeature UseCounter name</h4>
            ${s.ot_webfeature_use_counter}`
        );
      }
      if (stageParts.length > 0 && s.ot_display_name) {
        stageParts.shift(
          html` <br /><br />
            <h4><strong>Origin Trial</strong> ${i}: ${s.ot_display_name}</h4>`
        );
      }
      parts.push(...stageParts);
    });
  }

  renderRisks() {
    const parts = [];

    // Interop risks
    const interopRisks = this.feature.interop_compat_risks;
    let interopRisksHTML = html`None`;
    if (interopRisks) {
      interopRisksHTML = html`<p class="preformatted">${interopRisks}</p>`;
    }
    parts.push(html`
      <br><br><h4>Interoperabiity and Compatibility</h4>
      ${interopRisksHTML}`);

    // Gecko risks
    parts.push(html`
      <br><br><i>Gecko:</i> ${this.feature.browsers.ff.view.text || html`None`}`);
    if (this.feature.browsers.ff.view.url) {
      parts.push(html`(<a href=${this.feature.browsers.ff.view.url}>${this.feature.browsers.ff.view.url}</a>)`);
    }
    const geckoNotes = this.feature.browsers.ff.view.notes;
    if (geckoNotes) {
      parts.push(geckoNotes);
    }

    // WebKit risks
    parts.push(html`
      <br><br><i>WebKit:</i> ${this.feature.browsers.safari.view.text || html`None`}`);
    if (this.feature.browsers.safari.view.url) {
      parts.push(html`(<a href=${this.feature.browsers.safari.view.url}>${this.feature.browsers.safari.view.url}</a>)`);
    }
    const webKitNotes = this.feature.browsers.safari.view.notes;
    if (webKitNotes) {
      parts.push(webKitNotes);
    }

    // Web developer risks
    parts.push(html`
      <br><br><i>Web developers</i>: ${this.feature.browsers.webdev.view.text || html`None`}`);
    if (this.feature.browsers.webdev.view.url) {
      parts.push(html`(<a href=${this.feature.browsers.webdev.view.url}>${this.feature.browsers.webdev.view.url}</a>)`);
    }
    const webdevNotes = this.feature.browsers.webdev.view.notes;
    if (webdevNotes) {
      parts.push(webdevNotes);
    }

    parts.push(html`
      <br><br><i>Other signals</i>:`);
    if (this.feature.browsers.other.view.notes) {
      parts.push(html`${this.feature.browsers.other.view.notes}`);
    }
    if (this.feature.ergonomics_risks) {
      parts.push(html`
        <br><br><h4>Ergonomics</h4>
        <p class="preformatted">${this.feature.ergonomics_risks}</p>
      `);
    }
    if (this.feature.activation_risks) {
      parts.push(html`
        <br><br><h4>Activation</h4>
        <p class="preformatted">${this.feature.activation_risks}</p>
      `);
    }
    if (this.feature.security_risks) {
      parts.push(html`
        <br><br><h4>Security</h4>
        <p class="preformatted">${this.feature.security_risks}</p>
      `);
    }
    parts.push(html`
      <br><br><h4>WebView application risks</h4>
      <p style="font-style: italic">
        Does this intent deprecate or change behavior of existing APIs,
        such that it has potentially high risk for Android WebView-based
        applications?
      </p>
      <p class="preformatted">${this.feature.webview_risks || html`None`}</p>
    `);

    return html`
      <br><br><h4>Risks</h4>
      <div style="margin-left: 4em;">
        ${parts}
      </div>
    `;
  }

  renderExperimentGoals() {
    // Only show this section for experiment intents.
    if (!(this.stage.stage_type in STAGE_TYPES_INTENT_EXPERIMENT)) return nothing;
    parts = [html`
      <br><br><h4>Goals for experimentation</h4>
      <p class="preformatted">${this.feature.experiment_goals}</p>`];
    if (this.feature.experiment_timeline) {
      parts.push(html`
        <br><br><h4>Experiment timeline</h4>
        <p class="preformatted">${this.feature.experiment_timeline}</p>`);
    }
    if (this.stage in OT_EXTENSION_STAGE_TYPES && this.stage.experiment_extension_reason) {
      parts.push(html`
        <br><br><h4>Reason this experiment is being extended</h4>
        <p class="preformatted">${stage.experiment_extension_reason}</p>
      `);
    }
    parts.push(html`
      <br><br><h4>Ongoing technical constraints</h4>
      <p class="preformatted">${this.feature.ongoing_constraints}</p>`);
    return html`${parts}`;
  }

  renderDebuggability() {
    return html`
      <br><br><h4>Debuggability</h4>
      <p class="preformatted">${this.feature.debuggability}</p>`;
  }

  renderAllPlatforms() {
    // This section is only shown for experimental and shipping intents.
    if (!(this.stage.stage_type in STAGE_TYPES_INTENT_EXPERIMENT)
        && !(this.stage.stage_type in STAGE_TYPES_SHIPPING)) return nothing;
    let descriptionHTML = html`None`;
    if (this.feature.all_platforms_descr) {
      descriptionHTML = html`<p class="preformatted">${this.feature.all_platforms_descr}</p>`;
    }
    return html`
      <br><br><h4>Will this feature be supported on all six Blink platforms
          (Windows, Mac, Linux, ChromeOS, Android, and Android WebView)?</h4>
      ${(this.feature.all_platforms) ? 'Yes' : 'No'}
      ${descriptionHTML}`;
  }

  renderWPT() {
    let descriptionHTML = html`None`;
    if (this.feature.wpt_descr) {
      descriptionHTML = html`<p class="preformatted">${this.feature.wpt_descr}</p>`;
    }
    return html`
      <br><br><h4>Is this feature fully tested by <a href="https://chromium.googlesource.com/chromium/src/+/main/docs/testing/web_platform_tests.md">web-platform-tests</a>?</h4>
      ${(this.feature.wpt) ? 'Yes' : 'No'}
      ${descriptionHTML}`;
  }

  renderDevTrialInstructions() {
    if (!this.feature.devtrial_instructions) return nothing;
    return html`
      <br><br><h4>DevTrial instructions</h4>
      <a href="${this.feature.devtrial_instructions}">${this.feature.devtrial_instructions}</a>`;
  }

  renderFlagName() {
    return html`
      <br><br><h4>Flag name on chrome://flags</h4>
      ${this.feature.flag_name}`;
  }

  renderFinchInfo() {
    const parts = [html`
      <br><br><h4>Finch feature name</h4>
      ${this.feature.finch_name}`];
    let nonFinchJustificationHTML = html`None`;
    if (this.feature.non_finch_justification) {
      nonFinchJustificationHTML = html`
        <p class="preformatted">${this.feature.non_finch_justification}</p>`;

    }
    parts.push(html`
      <br><br><h4>Non-finch justification</h4>
      ${nonFinchJustificationHTML}`);
    return html`${parts}`;
  }

  renderEmbedderSupport() {
    return html`
      <br><br><h4>Requires code in //chrome?</h4>
      ${this.feature.requires_embedder_support}`;
  }



  renderEmailBody() {
    return [
      this.renderOwners(),
      this.renderExplainerLinks(),
      this.renderSpecification(),
      this.renderDesignDocs(),
      this.renderSummary(),
      this.renderBlinkComponents(),
      this.renderMotivation(),
      this.renderInitialPublicProposal(),
      this.renderTags(),
      this.renderTagReview(),
      this.renderOTInfo(),
      this.renderRisks(),
      this.renderExperimentGoals(),
      this.renderDebuggability(),
      this.renderAllPlatforms(),
      this.renderWPT(),
      this.renderDevTrialInstructions(),
      this.renderFlagName(),
      this.renderFinchInfo(),
      this.renderEmbedderSupport(),
    ];
  }

  render() {
    console.log(this.feature);
    return html`
      <p>Email to</p>
      <div class="subject email-content-div">blink-dev@chromium.org</div>

      <p>Subject</p>
      <div class="subject email-content-div">
        ${this.computeSubjectPrefix()}: ${this.feature.name}
      </div>

      <!-- Insted of vertical margins, <br> elements are used to create line breaks -->
      <!-- that can be copied and pasted into a text editor. -->

      <p>
        Body
        <span
          class="tooltip copy-text"
          style="float:right"
          title="Copy text to clipboard"
        >
          <a href="#" data-tooltip>
            <iron-icon
              icon="chromestatus:content_copy"
              id="copy-email-body"
            ></iron-icon>
          </a>
        </span>
      </p>

      <div class="email email-content-div">${this.renderEmailBody()}</div>
    `;
  }
}

customElements.define('chromedash-intent-template', ChromedashIntentTemplate);
