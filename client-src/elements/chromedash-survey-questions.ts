import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict, User} from '../js-src/cs-client';
import {GateDict} from './chromedash-gate-chip';
import {GATE_TYPES} from './form-field-enums.js';
import {GATE_QUESTIONNAIRES} from './gate-details.js';
import {autolink} from './utils.js';

@customElement('chromedash-survey-questions')
export class ChromedashGateColumn extends LitElement {

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

  //@property({type: Object})
  //user!: User;
  //@state()
  //feature!: Feature;
  @state()
  gate!: GateDict;
  //@state()
  //submitting = false;
  @state()
  loading = true;


  renderQuestionnaireSkeleton(): TemplateResult {
    return html`
      <!-- prettier-ignore -->
      <div id="questionnaire">Loading...</div>
      <p class="instructions">&nbsp;</p>
    `;
  }

  renderBooleanField(name: string, desc: string): TemplateResult {
    return html`
    <li class="question">
    <sl-checkbox name="${name}"></sl-checkbox>
    ${desc}
    </li>
    `;
  }

  renderStringField(name: string, desc: string): TemplateResult {
    return html`
    <li class="question">
    ${desc}
    <sl-input name="${name}" size="small"></sl-input>
    </li>
    `;
  }

  renderPrivacyForm(): TemplateResult {
    return html`
    <div id="questionnaire">
    <ol>
      ${this.renderBooleanField(
        "is_language_polyfill",
        "a long description that takes up more than one full line.")}
      ${this.renderBooleanField(
        "field",
        "desc")}
      ${this.renderBooleanField(
        "field",
        "desc")}
      ${this.renderStringField(
        "field",
        "desc that kind of goes a long way")}
        </ol>
    </div>
    `;
  }

  renderQuestionnaire(): TemplateResult {
    if (this.gate.gate_type === GATE_TYPES.PRIVACY_ORIGIN_TRIAL ||
      this.gate.gate_type === GATE_TYPES.PRIVACY_SHIP) {
        return this.renderPrivacyForm();
    }
    const questionnaireText = GATE_QUESTIONNAIRES[this.gate.gate_type];
    if (!questionnaireText) return html``;
    const markup =
      typeof questionnaireText == 'string'
        ? autolink(questionnaireText)
        : questionnaireText;
    return html`
      <!-- prettier-ignore -->
      <div id="questionnaire">${markup}</div>
      <p class="instructions">Please post responses in the comments below.</p>
    `;
  }

  render(): TemplateResult {
    return html`
    <h2>Survey questions</h2>
    ${this.loading ?
      this.renderQuestionnaireSkeleton() :
      this.renderQuestionnaire()}
    `;
  }

}
