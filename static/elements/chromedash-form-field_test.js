import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormField} from './chromedash-form-field';
import {slotAssignedElements} from './utils';

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
});
