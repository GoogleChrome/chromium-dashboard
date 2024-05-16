import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  GATE_TYPES,
  FEATURE_TYPES,
  INTENT_STAGES,
  STAGE_TYPES_INTENT_EXPERIMENT,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_PROTOTYPE,
  STAGE_TYPES_SHIPPING,
  OT_EXTENSION_STAGE_TYPES,
  STAGE_BLINK_EVAL_READINESS,
  STAGE_TYPES_DEV_TRIAL,
} from './form-field-enums.js';
import {showToastMessage} from './utils.js';

class ChromedashIntentTemplate extends LitElement {
  static get properties() {
    return {
      appTitle: {type: String},
      feature: {type: Object},
      stage: {type: Object},
      gate: {type: Object},
      processStage: {type: Object},
      displayFeatureUnlistedWarning: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.appTitle = '';
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
        table {
          tr[hidden] {
            th,
            td {
              padding: 0;
            }
          }

          th {
            padding: 12px 10px 5px 0;
            vertical-align: top;
          }

          td {
            padding: 6px 10px;
            vertical-align: top;
          }

          td:first-of-type {
            width: 60%;
          }

          .helptext {
            display: block;
            font-size: small;
            max-width: 40em;
            margin-top: 2px;
          }

          input[type='text'],
          input[type='url'],
          input[type='email'],
          textarea {
            width: 100%;
            font: var(--form-element-font);
          }

          select {
            max-width: 350px;
          }

          :required {
            border: 1px solid $chromium-color-dark;
          }

          .interacted:valid {
            border: 1px solid green;
          }

          .interacted:invalid {
            border: 1px solid $invalid-color;
          }

          input:not([type='submit']):not([type='search']) {
            outline: 1px dotted var(--error-border-color);
            background-color: #ffedf5;
          }
        }
      `,
    ];
  }

  setCopyEmailListener() {
    const copyEmailBodyEl = this.shadowRoot.querySelector('#copy-email-body');
    const emailBodyEl = this.shadowRoot.querySelector('.email');
    if (copyEmailBodyEl && emailBodyEl) {
      copyEmailBodyEl.addEventListener('click', () => {
        navigator.clipboard.writeText(emailBodyEl.innerText);
        showToastMessage('Email body copied');
      });
    }
  }

  firstUpdated() {
    // We need to wait until the entire page is rendered, so later dependents
    // are available, hence firstUpdated is too soon.
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () =>
        setTimeout(() => {
          this.setCopyEmailListener();
        })
      );
    } else {
      this.setCopyEmailListener();
    }
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
          html`<a
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
    const parts = [
      html` <br /><br />
        <h4>TAG Review</h4>
        ${this.feature.tag_review || 'None'}`,
    ];
    const tagReviewStatus = this.feature.tag_review_status;
    if (tagReviewStatus) {
      parts.push(
        html` <br /><br />
          <h4>TAG review status</h4>
          ${this.feature.tag_review_status}`
      );
    }
    return html`${parts}`;
  }

  renderOTInfo(otStages) {
    if (otStages.length === 0) return nothing;
    const parts = [];
    otStages.forEach((s, i) => {
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
            <h4>
              <strong>Origin Trial</strong> ${i + 1}: ${s.ot_display_name}
            </h4>`
        );
      }
      parts.push(...stageParts);
    });
    return html`${parts}`;
  }

  renderRisks() {
    const parts = [];

    // Interop risks
    const interopRisks = this.feature.interop_compat_risks;
    let interopRisksHTML = html`None`;
    if (interopRisks) {
      interopRisksHTML = html`<p class="preformatted">${interopRisks}</p>`;
    }
    parts.push(
      html` <br /><br />
        <h4>Interoperabiity and Compatibility</h4>
        ${interopRisksHTML}`
    );

    // Gecko risks
    parts.push(
      html` <br /><br /><i>Gecko:</i> ${this.feature.browsers.ff.view.text ||
        html`None`}`
    );
    if (this.feature.browsers.ff.view.url) {
      parts.push(
        html`(<a href="${this.feature.browsers.ff.view.url}"
            >${this.feature.browsers.ff.view.url}</a
          >)`
      );
    }
    const geckoNotes = this.feature.browsers.ff.view.notes;
    if (geckoNotes) {
      parts.push(geckoNotes);
    }

    // WebKit risks
    parts.push(
      html` <br /><br /><i>WebKit:</i> ${this.feature.browsers.safari.view
          .text || html`None`}`
    );
    if (this.feature.browsers.safari.view.url) {
      parts.push(
        html`(<a href="${this.feature.browsers.safari.view.url}"
            >${this.feature.browsers.safari.view.url}</a
          >)`
      );
    }
    const webKitNotes = this.feature.browsers.safari.view.notes;
    if (webKitNotes) {
      parts.push(webKitNotes);
    }

    // Web developer risks
    parts.push(
      html` <br /><br /><i>Web developers</i>:
        ${this.feature.browsers.webdev.view.text || html`None`}`
    );
    if (this.feature.browsers.webdev.view.url) {
      parts.push(
        html`(<a href="${this.feature.browsers.webdev.view.url}"
            >${this.feature.browsers.webdev.view.url}</a
          >)`
      );
    }
    const webdevNotes = this.feature.browsers.webdev.view.notes;
    if (webdevNotes) {
      parts.push(webdevNotes);
    }

    parts.push(html` <br /><br /><i>Other signals</i>:`);
    if (this.feature.browsers.other.view.notes) {
      parts.push(html`${this.feature.browsers.other.view.notes}`);
    }
    if (this.feature.ergonomics_risks) {
      parts.push(html`
        <br /><br />
        <h4>Ergonomics</h4>
        <p class="preformatted">${this.feature.ergonomics_risks}</p>
      `);
    }
    if (this.feature.activation_risks) {
      parts.push(html`
        <br /><br />
        <h4>Activation</h4>
        <p class="preformatted">${this.feature.activation_risks}</p>
      `);
    }
    if (this.feature.security_risks) {
      parts.push(html`
        <br /><br />
        <h4>Security</h4>
        <p class="preformatted">${this.feature.security_risks}</p>
      `);
    }
    parts.push(html`
      <br /><br />
      <h4>WebView application risks</h4>
      <p style="font-style: italic">
        Does this intent deprecate or change behavior of existing APIs, such
        that it has potentially high risk for Android WebView-based
        applications?
      </p>
      <p class="preformatted">${this.feature.webview_risks || html`None`}</p>
    `);

    return html`
      <br /><br />
      <h4>Risks</h4>
      <div style="margin-left: 4em;">${parts}</div>
    `;
  }

  renderExperimentGoals() {
    // Only show this section for experiment intents.
    if (!STAGE_TYPES_INTENT_EXPERIMENT.has(this.stage.stage_type))
      return nothing;
    const parts = [
      html` <br /><br />
        <h4>Goals for experimentation</h4>
        <p class="preformatted">${this.feature.experiment_goals || ''}</p>`,
    ];
    if (this.feature.experiment_timeline) {
      parts.push(
        html` <br /><br />
          <h4>Experiment timeline</h4>
          <p class="preformatted">${this.feature.experiment_timeline}</p>`
      );
    }
    if (
      OT_EXTENSION_STAGE_TYPES.has(this.stage.stage_type) &&
      this.stage.experiment_extension_reason
    ) {
      parts.push(html`
        <br /><br />
        <h4>Reason this experiment is being extended</h4>
        <p class="preformatted">${stage.experiment_extension_reason}</p>
      `);
    }
    parts.push(
      html` <br /><br />
        <h4>Ongoing technical constraints</h4>
        ${this.feature.ongoing_constraints || 'None'}`
    );
    return html`${parts}`;
  }

  renderDebuggability() {
    return html` <br /><br />
      <h4>Debuggability</h4>
      <p class="preformatted">${this.feature.debuggability || 'None'}</p>`;
  }

  renderAllPlatforms() {
    // This section is only shown for experimental and shipping intents.
    if (
      !STAGE_TYPES_INTENT_EXPERIMENT.has(this.stage.stage_type) &&
      !STAGE_TYPES_SHIPPING.has(this.stage.stage_type)
    )
      return nothing;
    let descriptionHTML = html`None`;
    if (this.feature.all_platforms_descr) {
      descriptionHTML = html`<p class="preformatted">
        ${this.feature.all_platforms_descr}
      </p>`;
    }
    return html` <br /><br />
      <h4>
        Will this feature be supported on all six Blink platforms (Windows, Mac,
        Linux, ChromeOS, Android, and Android WebView)?
      </h4>
      ${this.feature.all_platforms ? 'Yes' : 'No'} ${descriptionHTML}`;
  }

  renderWPT() {
    let descriptionHTML = nothing;
    if (this.feature.wpt_descr) {
      descriptionHTML = html`<br />
        <p class="preformatted">${this.feature.wpt_descr}</p>`;
    }
    return html` <br /><br />
      <h4>
        Is this feature fully tested by
        <a
          href="https://chromium.googlesource.com/chromium/src/+/main/docs/testing/web_platform_tests.md"
          >web-platform-tests</a
        >?
      </h4>
      ${this.feature.wpt ? 'Yes' : 'No'} ${descriptionHTML}`;
  }

  renderDevTrialInstructions() {
    if (!this.feature.devtrial_instructions) return nothing;
    return html` <br /><br />
      <h4>DevTrial instructions</h4>
      <a href="${this.feature.devtrial_instructions}"
        >${this.feature.devtrial_instructions}</a
      >`;
  }

  renderFlagName() {
    return html` <br /><br />
      <h4>Flag name on chrome://flags</h4>
      ${this.feature.flag_name || 'None'}`;
  }

  renderFinchInfo() {
    const parts = [
      html` <br /><br />
        <h4>Finch feature name</h4>
        ${this.feature.finch_name || 'None'}`,
    ];
    let nonFinchJustificationHTML = html`None`;
    if (this.feature.non_finch_justification) {
      nonFinchJustificationHTML = html` <p class="preformatted">
        ${this.feature.non_finch_justification}
      </p>`;
    }
    parts.push(
      html` <br /><br />
        <h4>Non-finch justification</h4>
        ${nonFinchJustificationHTML}`
    );
    return html`${parts}`;
  }

  renderEmbedderSupport() {
    return html` <br /><br />
      <h4>Requires code in //chrome?</h4>
      ${this.feature.requires_embedder_support ? 'Yes' : 'No'}`;
  }

  renderTrackingBug() {
    if (!this.feature.browsers.chrome.bug) return nothing;
    return html` <br /><br />
      <h4>Tracking bug</h4>
      <a href="${this.feature.browsers.chrome.bug}"
        >${this.feature.browsers.chrome.bug}</a
      >`;
  }

  renderLaunchBug() {
    if (!this.feature.launch_bug_url) return nothing;
    return html` <br /><br />
      <h4>Launch bug</h4>
      <a href="${this.feature.launch_bug_url}"
        >${this.feature.launch_bug_url}</a
      >`;
  }

  renderMeasurement() {
    if (!this.feature.measurement) return nothing;
    return html` <br /><br />
      <h4>Measurement</h4>
      ${this.feature.measurement}`;
  }

  renderAvailabilityExpectation() {
    if (!this.feature.availability_expectation) return nothing;
    return html` <br /><br />
      <h4>Availability expectation</h4>
      ${this.feature.availability_expectation}`;
  }

  renderAdoptionExpectation() {
    if (!this.feature.adoption_expectation) return nothing;
    return html` <br /><br />
      <h4>Adoption expectation</h4>
      ${this.feature.adoption_expectation}`;
  }

  renderAdoptionPlan() {
    if (!this.feature.adoption_plan) return nothing;
    return html` <br /><br />
      <h4>Adoption plan</h4>
      ${this.feature.adoption_plan}`;
  }

  renderNonOSSDeps() {
    if (!this.feature.non_oss_deps) return nothing;
    return html` <br /><br />
      <h4>Non-OSS dependencies</h4>
      <p style="font-style: italic">
        Does the feature depend on any code or APIs outside the Chromium open
        source repository and its open-source dependencies to function?
      </p>

      ${this.feature.non_oss_deps}`;
  }

  renderSampleLinks() {
    // Only show for shipping stages.
    if (
      !STAGE_TYPES_SHIPPING.has(this.stage.stage_type) &&
      !this.stage.stage_type !== STAGE_BLINK_EVAL_READINESS
    ) {
      return nothing;
    }
    return html` <br /><br />
      <h4>Sample links</h4>
      ${this.feature.resource.samples.map(
        url => html`<br /><a href="${url}">${url}</a>`
      )}`;
  }

  renderDesktopMilestonesTable(dtStages, otStages, shipStages) {
    const shipStagesHTML = shipStages.map(s => {
      if (!s.desktop_first) {
        return nothing;
      }
      return html` <tr>
        <td>Shipping on desktop</td>
        <td>${s.desktop_first}</td>
      </tr>`;
    });

    const otStagesHTML = otStages.map((s, i) => {
      const parts = [];
      const identifier = otStages.length > 1 ? `${i + 1} ` : '';
      if (s.desktop_first) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}desktop first</td>
            <td>${s.desktop_first}</td>
          </tr>`
        );
      }
      if (s.desktop_last) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}desktop last</td>
            <td>${s.desktop_last}</td>
          </tr>`
        );
      }
      s.extensions.forEach((es, j) => {
        const extensionIdentifier = s.extensions.length > 1 ? `${j + 1} ` : '';
        if (es.desktop_last) {
          parts.push(
            html` <tr>
              <td>
                Origin trial ${identifier}extension ${extensionIdentifier}end
                milestone
              </td>
              <td>${es.desktop_last}</td>
            </tr>`
          );
        }
      });
      return html`${parts}`;
    });

    const dtStagesHTML = dtStages.map(s => {
      if (!s.desktop_first) {
        return nothing;
      }
      return html` <tr>
        <td>DevTrial on desktop</td>
        <td>${s.desktop_first}</td>
      </tr>`;
    });
    return html` <table>
      ${shipStagesHTML}${otStagesHTML}${dtStagesHTML}
    </table>`;
  }

  renderAndroidMilestonesTable(dtStages, otStages, shipStages) {
    const shipStagesHTML = shipStages.map(s => {
      if (!s.android_first) {
        return nothing;
      }
      return html` <tr>
        <td>Shipping on Android</td>
        <td>${s.android_first}</td>
      </tr>`;
    });

    const otStagesHTML = otStages.map((s, i) => {
      const parts = [];
      const identifier = otStages.length > 1 ? `${i + 1} ` : '';
      if (s.android_first) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}Android first</td>
            <td>${s.android_first}</td>
          </tr>`
        );
      }
      if (s.android_last) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}Android last</td>
            <td>${s.android_last}</td>
          </tr>`
        );
      }
      return html`${parts}`;
    });

    const dtStagesHTML = dtStages.map(s => {
      if (!s.android_first) {
        return nothing;
      }
      return html` <tr>
        <td>DevTrial on Android</td>
        <td>${s.android_first}</td>
      </tr>`;
    });
    return html` <table>
      ${shipStagesHTML}${otStagesHTML}${dtStagesHTML}
    </table>`;
  }

  renderWebViewMilestonesTable(otStages, shipStages) {
    const shipStagesHTML = shipStages.map(s => {
      if (!s.webview_first) {
        return nothing;
      }
      return html` <tr>
        <td>Shipping on WebView</td>
        <td>${s.webview_first}</td>
      </tr>`;
    });

    const otStagesHTML = otStages.map((s, i) => {
      const parts = [];
      const identifier = otStages.length > 1 ? `${i + 1} ` : '';
      if (s.webview_first) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}WebView first</td>
            <td>${s.webview_first}</td>
          </tr>`
        );
      }
      if (s.webview_last) {
        parts.push(
          html` <tr>
            <td>Origin trial ${identifier}WebView last</td>
            <td>${s.webview_last}</td>
          </tr>`
        );
      }
      return html`${parts}`;
    });
    return html` <table>
      ${shipStagesHTML}${otStagesHTML}
    </table>`;
  }

  renderIOSMilestonesTable(shipStages, dtStages) {
    const shipStagesHTML = shipStages.map(s => {
      if (!s.ios_first) {
        return nothing;
      }
      return html` <tr>
        <td>Shipping on iOS</td>
        <td>${s.ios_first}</td>
      </tr>`;
    });

    const dtStagesHTML = dtStages.map(s => {
      if (!s.ios_first) {
        return nothing;
      }
      return html` <tr>
        <td>DevTrial on iOS</td>
        <td>${s.ios_first}</td>
      </tr>`;
    });
    return html` <table>
      ${shipStagesHTML}${dtStagesHTML}
    </table>`;
  }

  renderEstimatedMilestones(dtStages, otStages, shipStages) {
    // Don't display the table if no milestones are defined.
    if (
      !(
        shipStages.some(
          s =>
            s.desktop_first || s.android_first || s.ios_first || s.webview_first
        ) ||
        otStages.some(
          s =>
            s.desktop_first ||
            s.android_first ||
            s.webview_first ||
            s.desktop_last ||
            s.android_last ||
            s.webview_last
        ) ||
        dtStages.some(s => s.desktop_first || s.android_first || s.ios_first)
      )
    ) {
      return html` <br /><br />
        <h4>Estimated milestones</h4>
        <p>No milestones specified</p>`;
    }
    return html` <br /><br />
      <h4>Estimated milestones</h4>
      ${this.renderDesktopMilestonesTable(dtStages, otStages, shipStages)}
      ${this.renderAndroidMilestonesTable(dtStages, otStages, shipStages)}
      ${this.renderWebViewMilestonesTable(otStages, shipStages)}
      ${this.renderIOSMilestonesTable(dtStages, shipStages)}`;
  }

  renderAnticipatedSpecChanges() {
    // Only show for shipping stages.
    if (
      !STAGE_TYPES_SHIPPING.has(this.stage.stage_type) ||
      this.feature.anticipated_spec_changes
    )
      return nothing;
    return html` <br /><br />
      <h4>Anticipated spec changes</h4>
      <p style="font-style: italic">
        Open questions about a feature may be a source of future web compat or
        interop issues. Please list open issues (e.g. links to known github
        issues in the project for the feature specification) whose resolution
        may introduce web compat/interop risk (e.g., changing to naming or
        structure of the API in a non-backward-compatible way).
      </p>

      ${this.feature.anticipated_spec_changes}`;
  }

  renderChromestatusLink() {
    const urlSuffix = `feature/${this.feature.id}?gate=${this.gate.id}`;
    const url = `${window.location.protocol}//${window.location.host}/${urlSuffix}`;
    return html` <br /><br />
      <h4>Link to entry on ${this.appTitle}</h4>
      <a href="${url}">${url}</a>`;
  }

  renderIntents(protoStages, dtStages, otStages, shipStages) {
    const parts = [];
    protoStages.forEach(s => {
      if (s.intent_thread_url) {
        parts.push(
          html` Intent to Prototype:
            <a href="${s.intent_thread_url}">${s.intent_thread_url}</a> <br />`
        );
      }
    });
    dtStages.forEach(s => {
      if (s.intent_thread_url) {
        parts.push(
          html` Ready for Trial:
            <a href="${s.intent_thread_url}">${s.intent_thread_url}</a> <br />`
        );
      }
    });
    otStages.forEach((s, i) => {
      const identifier = otStages.length > 1 ? ` ${i + 1}` : '';
      if (s.intent_thread_url) {
        parts.push(
          html`Intent to Experiment${identifier}:
            <a href="${s.intent_thread_url}">${s.intent_thread_url}</a> <br />`
        );
      }
      s.extensions.forEach((es, j) => {
        const extensionIdentifier =
          s.extensions.length > 1 ? ` (Extension ${j + 1})` : '';
        if (es.intent_thread_url) {
          parts.push(
            html` Intent to Extend Experiment${extensionIdentifier}:
              <a href="${es.intent_thread_url}">${es.intent_thread_url}</a>
              <br />`
          );
        }
      });
    });
    shipStages.forEach(s => {
      if (s.intent_thread_url) {
        parts.push(
          html` Intent to Ship:
            <a href="${s.intent_thread_url}">${s.intent_thread_url}</a> <br />`
        );
      }
    });

    if (parts.length === 0) return nothing;
    return html` <br /><br />
      <h4>Links to previous Intent discussions</h4>

      ${parts}`;
  }

  renderFooterNote() {
    const url = `${window.location.protocol}//${window.location.host}/`;
    return html` <br /><br />
      <div>
        <small>
          This intent message was generated by
          <a href="${url}">${this.appTitle}</a>.
        </small>
      </div>`;
  }

  renderEmailBody() {
    const protoStages = this.feature.stages.filter(s =>
      STAGE_TYPES_PROTOTYPE.has(s.stage_type)
    );
    const dtStages = this.feature.stages.filter(s =>
      STAGE_TYPES_DEV_TRIAL.has(s.stage_type)
    );
    const otStages = this.feature.stages.filter(s =>
      STAGE_TYPES_ORIGIN_TRIAL.has(s.stage_type)
    );
    const shipStages = this.feature.stages.filter(s =>
      STAGE_TYPES_SHIPPING.has(s.stage_type)
    );
    return html` ${[
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
      this.renderOTInfo(otStages),
      this.renderRisks(),
      this.renderExperimentGoals(),
      this.renderDebuggability(),
      this.renderAllPlatforms(),
      this.renderWPT(),
      this.renderDevTrialInstructions(),
      this.renderFlagName(),
      this.renderFinchInfo(),
      this.renderEmbedderSupport(),
      this.renderTrackingBug(),
      this.renderLaunchBug(),
      this.renderMeasurement(),
      this.renderAvailabilityExpectation(),
      this.renderAdoptionExpectation(),
      this.renderAdoptionPlan(),
      this.renderNonOSSDeps(),
      this.renderSampleLinks(),
      this.renderEstimatedMilestones(dtStages, otStages, shipStages),
      this.renderAnticipatedSpecChanges(),
      this.renderChromestatusLink(),
      this.renderIntents(protoStages, dtStages, otStages, shipStages),
      this.renderFooterNote(),
    ]}`;
  }

  render() {
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
          <iron-icon
            icon="chromestatus:content_copy"
            id="copy-email-body"
          ></iron-icon>
        </span>
      </p>

      <div class="email email-content-div">${this.renderEmailBody()}</div>
    `;
  }
}

customElements.define('chromedash-intent-template', ChromedashIntentTemplate);
