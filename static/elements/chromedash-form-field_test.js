import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormField} from './chromedash-form-field';

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

    const firstRow = component.shadowRoot.querySelector('tr');
    assert.exists(firstRow);
    assert.exists(firstRow.querySelector('slot[name="label"'));

    const secondRow = component.shadowRoot.querySelector('tr:nth-child(2)');
    assert.exists(secondRow);
    assert.exists(secondRow.querySelector('slot[name="error"'));
    assert.exists(secondRow.querySelector('slot[name="field"'));
    assert.exists(secondRow.querySelector('slot[name="help"'));
  });

});
