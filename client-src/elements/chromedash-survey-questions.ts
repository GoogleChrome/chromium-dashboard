import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {SlChangeEvent, SlInput} from '@shoelace-style/shoelace';
import {Feature, StageDict, User} from '../js-src/cs-client';
import {GateDict} from './chromedash-gate-chip';
import {GATE_TYPES} from './form-field-enums.js';
import {GATE_QUESTIONNAIRES} from './gate-details.js';
import {autolink} from './utils.js';

@customElement('chromedash-survey-questions')
export class ChromedashSurveyQuestions extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #questionnaire {
          padding: var(--content-padding-half);
          border-radius: var(--border-radius);
          background: var(--table-alternate-background);
        }
        #questionnaire * + * {
          padding-top: var(--content-padding);
        }
        #questionnaire ul {
          padding-left: 1em;
        }
        #questionnaire ul li {
          list-style: disc;
        }
        #questionnaire ol li {
          list-style: auto;
          margin-left: var(--content-padding);
        }
        .question {
          padding: var(--content-padding-half);
        }
        .instructions {
          padding: var(--content-padding-half);
          margin-bottom: var(--content-padding-large);
        }
      `,
    ];
  }

  @state()
  feature!: Feature;
  @state()
  gate!: GateDict;
  @state()
  loading = true;

  refetch() {
    window.csClient.getGates(this.feature.id).then(resp => {
      for (const g of resp.gates) {
        if (g.id === this.gate.id) {
          this.gate = g;
          break;
        }
      }
    });
  }

  renderQuestionnaireSkeleton(): TemplateResult {
    return html`
      <div id="questionnaire">Loading...</div>
      <p class="instructions">&nbsp;</p>
    `;
  }

  handleFieldChange(name: string, value: string | boolean) {
    window.csClient
      .updateGate(this.feature.id, this.gate.id, null, {[name]: value})
      .then(() => {
        this.refetch();
      });
  }

  renderBooleanField(name: string, desc: string): TemplateResult {
    const value: boolean = this.gate.survey_answers?.[name];
    return html`
      <li class="question">
        <sl-checkbox
          name=${name}
          ?checked=${value}
          @sl-change=${e => this.handleFieldChange(name, e.target?.checked)}
        ></sl-checkbox>
        ${desc}
      </li>
    `;
  }

  renderStringField(name: string, desc: string): TemplateResult {
    const value: string = this.gate.survey_answers?.[name];
    return html`
      <li class="question">
        ${desc}
        <sl-input
          name="${name}"
          size="small"
          value=${value}
          @sl-change=${e => this.handleFieldChange(name, e.target?.value)}
        ></sl-input>
      </li>
    `;
  }

  renderPrivacyForm(): TemplateResult {
    return html`
      <div id="questionnaire">
        <ol>
          ${this.renderBooleanField(
            'is_language_polyfill',
            `This is a new JS language construct that has already
         been polyfillable.`
          )}
          ${this.renderBooleanField(
            'is_api_polyfill',
            `This is a new API that ergonomically provides a function
         that was already polyfillable under the same conditions.
         By "same conditions" we mean, for example, that if a
         polyfill was only possible when the user has granted a
         certain permission, the API respects the same permission.`
          )}
          ${this.renderBooleanField(
            'is_same_origin_css',
            `This is a CSS addition or change such that the style only
         depends on same-origin information and does NOT on user data.
           CSS changes are usually benign, however: if the style relies
         on iframes or subresources, it could reveal cross-origin
           information.  If the style depends on user data, such as
          browsing history (like :visited), cookies, or user input
        (like hidden=until-found), the style could be used by the
        website to read this data.`
          )}
          ${this.renderStringField(
            'launch_or_contact',
            `If there is a Google-internal launch entry filed for this
         exact same issue, enter its URL here. Or, if this has previously
        been discussed with someone on the privacy team, enter their
        email address. Or, enter "None".`
          )}
        </ol>
      </div>
    `;
  }

  renderQuestionnaire(): TemplateResult {
    if (
      this.gate.gate_type === GATE_TYPES.PRIVACY_ORIGIN_TRIAL ||
      this.gate.gate_type === GATE_TYPES.PRIVACY_SHIP
    ) {
      return this.renderPrivacyForm();
    }
    const questionnaireText = GATE_QUESTIONNAIRES[this.gate.gate_type];
    if (!questionnaireText) return html`No questions`;
    const markup =
      typeof questionnaireText == 'string'
        ? autolink(questionnaireText)
        : questionnaireText;
    return html`
      <div id="questionnaire">${markup}</div>
      <p class="instructions">Please post responses in the comments below.</p>
    `;
  }

  render(): TemplateResult {
    return html`
      <h2>Survey questions</h2>
      ${this.loading
        ? this.renderQuestionnaireSkeleton()
        : this.renderQuestionnaire()}
    `;
  }
}
