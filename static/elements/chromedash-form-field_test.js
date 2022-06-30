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
    const fieldRow = component.shadowRoot.querySelector('tr');
    assert.exists(fieldRow);
  });

  it('renders with slots for label, field, error, help', async () => {
    const component = await fixture(
      html`
      <chromedash-form-field>
        <span slot="label">Label</span>
        <span slot="field">Field</span>
        <span slot="error">Error</span>
        <span slot="help">Help</span>
      </chromedash-form-field>`);
    assert.exists(component);
    await component.updateComplete;

    const labelElements = slotAssignedElements(component, 'label');
    assert.exists(labelElements);
    assert.include(labelElements[0].innerHTML, 'Label');

    const fieldElements = slotAssignedElements(component, 'field');
    assert.exists(fieldElements);
    assert.include(fieldElements[0].innerHTML, 'Field');

    const errorElements = slotAssignedElements(component, 'error');
    assert.exists(errorElements);
    assert.include(errorElements[0].innerHTML, 'Error');

    const helpElements = slotAssignedElements(component, 'help');
    assert.exists(helpElements);
    assert.include(helpElements[0].innerHTML, 'Help');
  });
});
