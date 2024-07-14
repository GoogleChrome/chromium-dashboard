import {assert, fixture} from '@open-wc/testing';
import '@shoelace-style/shoelace/dist/components/option/option.js';
import {html} from 'lit';
import {ChromedashFormField} from './chromedash-form-field';
import {
  STAGE_BLINK_INCUBATE,
  STAGE_BLINK_ORIGIN_TRIAL,
  STAGE_BLINK_SHIPPING,
} from './form-field-enums';

describe('chromedash-form-field', () => {
  it('renders a checkbox type of field', async () => {
    const component = await fixture(
      html` <chromedash-form-field
        name="unlisted"
        value="True"
        checked="True"
        checkboxLabel="A specific label"
      >
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Unlisted');
    assert.include(renderElement.innerHTML, 'sl-checkbox');
    assert.include(renderElement.innerHTML, 'checked');
    assert.include(renderElement.innerHTML, 'A specific label');
  });

  it('renders a select type of field', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="category" value="0">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'category');
    assert.include(renderElement.innerHTML, 'sl-select');
    assert.include(renderElement.innerHTML, 'sl-option');
  });

  it('renders a input type of field (with extraHelp)', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="name" value="">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Feature name');
    assert.include(renderElement.innerHTML, 'sl-input');
    assert.include(renderElement.innerHTML, 'required');
    assert.include(renderElement.innerHTML, 'sl-icon-button');
    assert.include(renderElement.innerHTML, 'class="extrahelp"');
  });

  it('renders a textarea type of field', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="summary" value="">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Summary');
    assert.include(renderElement.innerHTML, 'chromedash-textarea');
    assert.include(renderElement.innerHTML, 'required');
  });

  it('renders a radios type of field', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="feature_type_radio_group" value="0">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Feature type');
    assert.include(renderElement.innerHTML, 'type="radio"');
    assert.include(renderElement.innerHTML, 'required');
  });

  it('renders a multiselect type of field', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="rollout_platforms">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Rollout platforms');
    assert.include(renderElement.innerHTML, 'sl-select');
    assert.include(renderElement.innerHTML, 'multiple');
    assert.include(renderElement.innerHTML, 'cleareable');
  });

  describe('complex fields', async () => {
    it('active_stage_id depends on the available stages', async () => {
      /** @type {import('./form-definition').FormattedFeature} */
      const formattedFeature = {
        stages: [
          {id: 1, stage_type: STAGE_BLINK_INCUBATE},
          {
            id: 2,
            stage_type: STAGE_BLINK_ORIGIN_TRIAL,
            display_name: 'Display name',
          },
          {
            id: 3,
            stage_type: STAGE_BLINK_ORIGIN_TRIAL,
          },
          {id: 4, stage_type: STAGE_BLINK_SHIPPING},
          {id: 5, stage_type: 9999, display_name: 'Not a stage type'},
        ],
      };
      const component = await fixture(html`
        <chromedash-form-field
          name="active_stage_id"
          .feature=${formattedFeature}
        ></chromedash-form-field>
      `);
      assert.instanceOf(component, ChromedashFormField);
      const optionValues = Array.from(
        component.renderRoot.querySelectorAll('sl-option')
      ).map(option => ({
        text: option.textContent!.trim(),
        value: option.value,
      }));
      assert.deepEqual(optionValues, [
        {text: 'Identify the need', value: '1'},
        {text: 'Origin trial: Display name', value: '2'},
        {text: 'Origin trial 2', value: '3'},
        {text: 'Prepare to ship', value: '4'},
      ]);
    });
  });
});
