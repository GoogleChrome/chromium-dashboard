import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormTable} from './chromedash-form-table';

describe('chromedash-form-table', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-form-table></chromedash-form-table>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormTable);
    const formContents = component.shadowRoot.querySelector('*');
    assert.exists(formContents);
  });

  it('renders with array of slots for rows', async () => {
    const component = await fixture(
      html`
      <chromedash-form-table>
      <span>Row 1</span>
      <span>Row 2</span>
      </chromedash-form-table>`);
    assert.exists(component);

    // console.log('component.innerHTML', component.innerHTML);
    // console.log('component.shadowRoot.innerHTML', component.shadowRoot.innerHTML);

    // const firstRow = component.shadowRoot.querySelector('span');
    // assert.exists(firstRow);

    // const secondRow = component.shadowRoot.querySelector('span:nth-child(2)');
    // assert.exists(secondRow);
  });
});
