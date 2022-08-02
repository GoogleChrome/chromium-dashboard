import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormField} from './chromedash-form-field';

describe('chromedash-form-field', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-form-field></chromedash-form-field>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormField);
    const fieldRow = component.renderRoot.querySelector('tr');
    assert.exists(fieldRow);
  });

  it('renders with attributes for field and error', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field field="Field" errors="Error">
      </chromedash-form-field>`);
    assert.exists(component);
    await component.updateComplete;

    const renderElement = component.renderRoot;

    assert.include(renderElement.innerHTML, 'Field');
    assert.include(renderElement.innerHTML, 'Error');
  });

  it('renders a checkbox type of field', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field name="unlisted" value="True" checked="True">
      </chromedash-form-field>`);
    await component.updateComplete;

    const renderElement = component.renderRoot;
    assert.include(renderElement.innerHTML, 'Unlisted');
    assert.include(renderElement.innerHTML, 'sl-checkbox');
    assert.include(renderElement.innerHTML, 'checked');
  });
});
