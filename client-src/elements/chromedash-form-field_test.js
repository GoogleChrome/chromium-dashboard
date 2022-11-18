import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormField} from './chromedash-form-field';

describe('chromedash-form-field', () => {
  it('renders a checkbox type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="unlisted" value="True" checked="True">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Unlisted');
    assert.include(renderElement.innerHTML, 'sl-checkbox');
    assert.include(renderElement.innerHTML, 'checked');
  });

  it('renders a select type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="category" value="0">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'category');
    assert.include(renderElement.innerHTML, 'sl-select');
    assert.include(renderElement.innerHTML, 'sl-menu-item');
  });

  it('renders a input type of field (with extraHelp)', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="name" value="">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Feature name');
    assert.include(renderElement.innerHTML, 'sl-input');
    assert.include(renderElement.innerHTML, 'required');
    assert.include(renderElement.innerHTML, 'sl-icon-button');
    assert.include(renderElement.innerHTML, 'class="extrahelp"');
  });

  it('renders a textarea type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="summary" value="">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Summary');
    assert.include(renderElement.innerHTML, 'chromedash-textarea');
    assert.include(renderElement.innerHTML, 'required');
  });

  it('renders a radios type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="feature_type_radio_group" value="0">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Feature type');
    assert.include(renderElement.innerHTML, 'type="radio"');
    assert.include(renderElement.innerHTML, 'required');
  });

  it('renders a multiselect type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="rollout_platforms" .value="[]">
      </chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Rollout platforms');
    assert.include(renderElement.innerHTML, 'sl-select');
    assert.include(renderElement.innerHTML, 'multiple');
    assert.include(renderElement.innerHTML, 'cleareable');
  });
});
