import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {SlCheckbox} from '@shoelace-style/shoelace';
import {ChromedashSurveyQuestions} from './chromedash-survey-questions';
import {ChromeStatusClient} from '../js-src/cs-client';
import {GATE_TYPES} from './form-field-enums';

describe('chromedash-survey-questions', () => {
  const unknownGate = {
    stage_id: 1,
    gate_id: 11,
    gate_type: 999,
  };

  const protoGate = {
    stage_id: 1,
    gate_id: 12,
    gate_type: GATE_TYPES.API_PROTOTYPE,
  };

  const privacyGate = {
    stage_id: 1,
    gate_id: 13,
    gate_type: GATE_TYPES.PRIVACY_SHIP,
    survey_answers: {
      is_language_polyfill: true,
      is_api_polyfill: false,
      is_same_origin_css: false,
      launch_or_contact: '',
    },
  };

  const uneditedPrivacyGate = {
    stage_id: 1,
    gate_id: 13,
    gate_type: GATE_TYPES.PRIVACY_SHIP,
    survey_answers: null,
  };

  const feature = {
    id: 123456789,
  };

  it('can be added to the page before being populated', async () => {
    const component = (await fixture(
      html`<chromedash-survey-questions></chromedash-survey-questions>`
    )) as ChromedashSurveyQuestions;
    assert.exists(component);
    assert.instanceOf(component, ChromedashSurveyQuestions);
    assert.include(component.shadowRoot!.innerHTML, 'Loading...');
  });

  it('copes with undefined gate types', async () => {
    const component = (await fixture(
      html`<chromedash-survey-questions
        .feature=${feature}
        .gate=${unknownGate}
        .loading=${false}
      ></chromedash-survey-questions>`
    )) as ChromedashSurveyQuestions;
    assert.exists(component);
    assert.instanceOf(component, ChromedashSurveyQuestions);
    assert.notInclude(component.shadowRoot!.innerHTML, 'Loading...');
    assert.include(component.shadowRoot!.innerHTML, 'No questions');
  });

  it('displays textual surveys', async () => {
    const component = (await fixture(
      html`<chromedash-survey-questions
        .feature=${feature}
        .gate=${protoGate}
        .loading=${false}
      ></chromedash-survey-questions>`
    )) as ChromedashSurveyQuestions;
    assert.exists(component);
    assert.instanceOf(component, ChromedashSurveyQuestions);
    assert.notInclude(component.shadowRoot!.innerHTML, 'Loading...');
    assert.include(component.shadowRoot!.innerHTML, 'post that message to');
  });

  it('displays the privacy surveys', async () => {
    const component = (await fixture(
      html`<chromedash-survey-questions
        .feature=${feature}
        .gate=${privacyGate}
        .loading=${false}
      ></chromedash-survey-questions>`
    )) as ChromedashSurveyQuestions;
    assert.exists(component);
    assert.instanceOf(component, ChromedashSurveyQuestions);
    assert.notInclude(component.shadowRoot!.innerHTML, 'Loading...');
    assert.include(component.shadowRoot!.innerHTML, 'JS language construct');
    const checkbox1 = component.shadowRoot!.querySelector(
      '[name=is_language_polyfill]'
    );
    assert.instanceOf(checkbox1, SlCheckbox);
    assert.isTrue(checkbox1.checked);
    const checkbox2 = component.shadowRoot!.querySelector(
      '[name=is_api_polyfill]'
    );
    assert.instanceOf(checkbox2, SlCheckbox);
    assert.isFalse(checkbox2.checked);
  });

  it('displays the privacy surveys even when nothing has been entered', async () => {
    const component = (await fixture(
      html`<chromedash-survey-questions
        .feature=${feature}
        .gate=${uneditedPrivacyGate}
        .loading=${false}
      ></chromedash-survey-questions>`
    )) as ChromedashSurveyQuestions;
    assert.exists(component);
    assert.instanceOf(component, ChromedashSurveyQuestions);
    assert.notInclude(component.shadowRoot!.innerHTML, 'Loading...');
    assert.include(component.shadowRoot!.innerHTML, 'JS language construct');
    const checkbox1 = component.shadowRoot!.querySelector(
      '[name=is_language_polyfill]'
    );
    assert.instanceOf(checkbox1, SlCheckbox);
    assert.isFalse(checkbox1.checked);
    const checkbox2 = component.shadowRoot!.querySelector(
      '[name=is_api_polyfill]'
    );
    assert.instanceOf(checkbox2, SlCheckbox);
    assert.isFalse(checkbox2.checked);
  });
});
