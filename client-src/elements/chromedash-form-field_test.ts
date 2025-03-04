import {assert, fixture} from '@open-wc/testing';
import '@shoelace-style/shoelace/dist/components/option/option.js';
import {html} from 'lit';
import {
  ChromedashFormField,
  enumLabelToFeatureKey,
} from './chromedash-form-field';
import {
  STAGE_BLINK_INCUBATE,
  STAGE_BLINK_ORIGIN_TRIAL,
  STAGE_BLINK_SHIPPING,
} from './form-field-enums';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

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

  it('renders Web Feature ID field with a link', async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    const webdxFeaturesStub = sinon.stub(window.csClient, 'getWebdxFeatures');
    webdxFeaturesStub.returns(Promise.resolve({}));

    const component = await fixture(
      html` <chromedash-form-field name="web_feature" value="hwb">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Web Feature ID');
    assert.include(renderElement.innerHTML, 'input');
    assert.include(renderElement.innerHTML, 'class="webdx"');
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

  it('renders an attachments type of field', async () => {
    const formattedFeature = {
      id: 12345,
    };
    const component = await fixture(
      html` <chromedash-form-field
        name="screenshot_links"
        value=""
        .feature=${formattedFeature}
      >
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot as HTMLElement;
    assert.include(renderElement.innerHTML, 'Screenshot link(s)');
    assert.include(renderElement.innerHTML, 'chromedash-attachments');
    assert.include(renderElement.innerHTML, 'multiple');
    assert.include(renderElement.innerHTML, 'Max size');
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

  it('skips unused obsolete multiselect choices', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="rollout_platforms">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);

    const slSelect = component.renderRoot.querySelector('sl-select');
    const inner = slSelect?.innerHTML;
    assert.include(inner, 'Android');
    assert.notInclude(inner, 'LaCrOS'); // It is obsolete.
    assert.include(inner, 'iOS');
  });

  it('includes used obsolete multiselect choices', async () => {
    const component = await fixture(
      html` <chromedash-form-field name="rollout_platforms" value="1,2,4">
      </chromedash-form-field>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);

    const slSelect = component.renderRoot.querySelector('sl-select');
    const inner = slSelect?.innerHTML;
    assert.include(inner, 'Android');
    assert.include(inner, 'LaCrOS'); // Obsoelete, but used.
    assert.include(inner, 'iOS');
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

  describe('enumLabelToFeatureKey', () => {
    it('should handle empty string', () => {
      assert.equal(enumLabelToFeatureKey(''), '');
    });

    it('should convert first character to lowercase', () => {
      assert.equal(enumLabelToFeatureKey('FooBar'), 'foo-bar');
      assert.equal(enumLabelToFeatureKey('Baz'), 'baz');
    });

    it('should add hyphen before uppercase letters', () => {
      assert.equal(enumLabelToFeatureKey('FooBarBaz'), 'foo-bar-baz');
      assert.equal(enumLabelToFeatureKey('ABC'), 'a-b-c');
    });

    it('should add hyphen before digits if preceded by a letter', () => {
      assert.equal(enumLabelToFeatureKey('Foo123'), 'foo-123');
      assert.equal(enumLabelToFeatureKey('AB1CD2'), 'a-b-1-c-d-2');
    });

    it('should not add hyphen before digits if not preceded by a letter', () => {
      assert.equal(enumLabelToFeatureKey('123ABC'), '123-a-b-c');
      assert.equal(enumLabelToFeatureKey('1A2B3C'), '1-a-2-b-3-c');
    });

    it('should handle mixed-case input', () => {
      assert.equal(enumLabelToFeatureKey('fOoBaR123'), 'f-oo-ba-r-123');
    });
  });
});
