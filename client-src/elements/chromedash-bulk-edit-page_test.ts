import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import {ChromedashBulkEditPage} from './chromedash-bulk-edit-page';

const CSV_FILE: string = `web-features,chromestatus
accent-color,https://chromestatus.com/feature/4752739957473280
align-content-block,https://chromestatus.com/feature/5159040328138752
`;

describe('chromedash-bulk-edit-page', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-bulk-edit-page></chromedash-bulk-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashBulkEditPage);

    // headers exists and with the correct text
    const subheaderDiv = component.shadowRoot!.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'Bulk edit');
    const previewHeader = component.shadowRoot!.querySelector('h3');
    assert.exists(previewHeader);
    assert.include(previewHeader.innerHTML, 'Preview');

    // file input element exists
    const fileInput = component.shadowRoot!.querySelector('input');
    assert.exists(fileInput);
    assert.equal(fileInput.type, 'file');

    // Initial instructions are displayed.
    const instr = component.shadowRoot!.querySelector('#instructions');
    assert.exists(instr);
    assert.include(instr.innerHTML, 'Select a CSV file');
  });

  it('parses file content', async () => {
    const component = await fixture(
      html`<chromedash-bulk-edit-page></chromedash-bulk-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashBulkEditPage);

    component.parseFileContent(CSV_FILE);
    assert.deepEqual(component.cells, [
      ['web-features', 'chromestatus'],
      ['accent-color', 'https://chromestatus.com/feature/4752739957473280'],
      [
        'align-content-block',
        'https://chromestatus.com/feature/5159040328138752',
      ],
    ]);

    assert.equal(component.featureIdIndex, 0);
    assert.equal(component.chromestatusUrlIndex, 1);
  });

  it('renders preview immediately', async () => {
    const component = await fixture(
      html`<chromedash-bulk-edit-page></chromedash-bulk-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashBulkEditPage);

    component.parseFileContent(CSV_FILE);
    await component.updateComplete;

    const table = component.shadowRoot!.querySelector('.data-table');
    assert.exists(table);
    assert.include(table.innerHTML, '<th>Row</th>');
    assert.include(table.innerHTML, 'accent-color</td>');
    assert.include(table.innerHTML, '/feature/4752739957473280');
    assert.include(table.innerHTML, '4752739957473280</a>');
    assert.include(table.innerHTML, 'align-content-block</td>');
    assert.include(table.innerHTML, '/feature/5159040328138752');
    assert.include(table.innerHTML, '5159040328138752</a>');
    assert.include(table.innerHTML, 'Loading...');
  });

  it('renders preview after fetching existing values', async () => {
    const component = await fixture(
      html`<chromedash-bulk-edit-page></chromedash-bulk-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashBulkEditPage);

    component.parseFileContent(CSV_FILE);
    component.items = [
      {
        row: 2,
        entryName: 'accent-color CSS property',
        csFid: 4752739957473280,
        desired: 'accent-color',
      },
      {
        row: 3,
        entryName: 'align-content CSS property for blocks',
        csFid: 5159040328138752,
        desired: 'align-content-block',
      },
    ];
    await component.updateComplete;

    const table = component.shadowRoot!.querySelector('.data-table');
    assert.exists(table);
    assert.include(table.innerHTML, '<th>Row</th>');
    assert.include(table.innerHTML, 'accent-color</td>');
    assert.include(table.innerHTML, '/feature/4752739957473280');
    assert.include(table.innerHTML, 'accent-color CSS property</a>');
    assert.notInclude(table.innerHTML, '4752739957473280</a>');
    assert.include(table.innerHTML, 'align-content-block</td>');
    assert.include(table.innerHTML, '/feature/5159040328138752');
    assert.include(
      table.innerHTML,
      'align-content CSS property for blocks</a>'
    );
    assert.notInclude(table.innerHTML, '5159040328138752</a>');
    assert.notInclude(table.innerHTML, 'Loading...');

    const diffsNew = component.shadowRoot!.querySelectorAll('.diff.new');
    assert.equal(diffsNew.length, 2);
    const diffsOld = component.shadowRoot!.querySelectorAll('.diff.old');
    assert.equal(diffsOld.length, 2);
  });

  it('renders preview after updating values', async () => {
    const component = await fixture(
      html`<chromedash-bulk-edit-page></chromedash-bulk-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashBulkEditPage);

    component.parseFileContent(CSV_FILE);
    component.items = [
      {
        row: 2,
        entryName: 'accent-color CSS property',
        csFid: 4752739957473280,
        existing: 'accent-color',
        desired: 'accent-color',
      },
      {
        row: 3,
        entryName: 'align-content CSS property for blocks',
        existing: 'align-content-block',
        csFid: 5159040328138752,
        desired: 'align-content-block',
      },
    ];
    await component.updateComplete;

    const table = component.shadowRoot!.querySelector('.data-table');
    assert.exists(table);
    assert.include(table.innerHTML, '<th>Row</th>');
    assert.include(table.innerHTML, 'accent-color</td>');
    assert.include(table.innerHTML, '/feature/4752739957473280');
    assert.include(table.innerHTML, 'accent-color CSS property</a>');
    assert.notInclude(table.innerHTML, '4752739957473280</a>');
    assert.include(table.innerHTML, 'align-content-block</td>');
    assert.include(table.innerHTML, '/feature/5159040328138752');
    assert.include(
      table.innerHTML,
      'align-content CSS property for blocks</a>'
    );
    assert.notInclude(table.innerHTML, '5159040328138752</a>');
    assert.notInclude(table.innerHTML, 'Loading...');

    const diffsNew = component.shadowRoot!.querySelectorAll('.diff.new');
    assert.equal(diffsNew.length, 0);
    const diffsOld = component.shadowRoot!.querySelectorAll('.diff.old');
    assert.equal(diffsOld.length, 0);
  });
});
