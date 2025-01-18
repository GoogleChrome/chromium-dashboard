import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict, User} from '../js-src/cs-client';
import {GateDict} from './chromedash-gate-chip';
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
        #questionnaire li {
          list-style: disc;
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
      <h2>Survey questions</h2>
      <!-- prettier-ignore -->
      <div id="questionnaire">Loading...</div>
      <p class="instructions">&nbsp;</p>
    `;
  }

  renderQuestionnaire(): TemplateResult {
    const questionnaireText = GATE_QUESTIONNAIRES[this.gate.gate_type];
    if (!questionnaireText) return html``;
    const markup =
      typeof questionnaireText == 'string'
        ? autolink(questionnaireText)
        : questionnaireText;
    return html`
      <h2>Survey questions</h2>
      <!-- prettier-ignore -->
      <div id="questionnaire">${markup}</div>
      <p class="instructions">Please post responses in the comments below.</p>
    `;
  }

  render(): TemplateResult {
    if (this.loading) {
      return this.renderQuestionnaireSkeleton();
    } else {
      return this.renderQuestionnaire();
    }
  }

}
