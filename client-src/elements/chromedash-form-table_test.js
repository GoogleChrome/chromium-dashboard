import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFormTable} from './chromedash-form-table';
import {slotAssignedElements} from './utils';

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
    await component.updateComplete;

    const children = slotAssignedElements(component, '');

    const firstRow = children[0];
    assert.exists(firstRow);
    assert.include(firstRow.innerHTML, 'Row 1');

    const secondRow = children[1];
    assert.exists(secondRow);
    assert.include(secondRow.innerHTML, 'Row 2');
  });

  // it('render for screenshot', async ({page}) => {
  //   const component = await fixture(
  //     html`<chromedash-form-table></chromedash-form-table>`);
  //   await component.updateComplete;
  //   assert.exists(component);

  //   const image = await component.toDataURL();
  //   assert.exists(image);

  //   // await page.screenshot({ path: 'screenshot.png', fullPage: true }).toMatchShapshot('screenshot.png');
  //   // done();
  // }).timeout(3000);
});
