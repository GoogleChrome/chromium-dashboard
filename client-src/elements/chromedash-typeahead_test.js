import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {
  ChromedashTypeahead,
  ChromedashTypeaheadDropdown,
  ChromedashTypeaheadItem,
} from './chromedash-typeahead';
import '@shoelace-style/shoelace/dist/components/input/input.js';
import '@shoelace-style/shoelace/dist/components/menu/menu.js';

describe('chromedash-typeahead', () => {
  it('reflects the value of the sl-input as its own value', async () => {
    const component = await fixture(html`
      <chromedash-typeahead> </chromedash-typeahead>
    `);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTypeahead);
    const slInput = component.shadowRoot.querySelector('sl-input');

    slInput.value = 'test value';
    component.reflectValue();
    assert.equal('test value', component.value);
  });

  it('has a menu that can show and hide', async () => {
    const component = await fixture(html`
      <chromedash-typeahead>
        <chromedash-typeahead-item
          id="item0"
          value="aaa"
          doc="Docs about aaa"
        ></chromedash-typeahead-item>
      </chromedash-typeahead>
    `);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTypeahead);
    const dropdown = component.shadowRoot.querySelector(
      'chromedash-typeahead-dropdown'
    );

    assert.equal(false, dropdown.open);

    component.show();
    assert.equal(true, dropdown.open);

    component.hide();
    assert.equal(false, dropdown.open);
  });

  it('can determine the prefix of what the user typed', async () => {
    const component = await fixture(html`
      <chromedash-typeahead>
        <chromedash-typeahead-item
          id="item0"
          value="aaa"
          doc="Docs about aaa"
        ></chromedash-typeahead-item>
      </chromedash-typeahead>
    `);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTypeahead);
    const slInput = component.shadowRoot.querySelector('sl-input');

    slInput.value = '';
    await slInput.updateComplete;
    component.findPrefix();
    assert.equal(0, component.chunkStart);
    assert.equal(0, component.chunkEnd);
    assert.equal('', component.prefix);

    slInput.value = 'term1 term2 term3';
    await slInput.updateComplete;
    slInput.input.selectionStart = 0;
    slInput.input.selectionEnd = 0;
    component.findPrefix();
    assert.equal(0, component.chunkStart);
    assert.equal(5, component.chunkEnd);
    assert.equal('', component.prefix);

    slInput.input.selectionStart = 0;
    slInput.input.selectionEnd = 3; // A range
    component.findPrefix();
    assert.equal(null, component.prefix);

    slInput.input.selectionStart = 14;
    slInput.input.selectionEnd = 14;
    component.findPrefix();
    assert.equal(12, component.chunkStart);
    assert.equal(17, component.chunkEnd);
    assert.equal('te', component.prefix);

    slInput.input.selectionStart = 17;
    slInput.input.selectionEnd = 17;
    component.findPrefix();
    assert.equal(12, component.chunkStart);
    assert.equal(17, component.chunkEnd);
    assert.equal('term3', component.prefix);
  });

  it('determines whether a candidate should be shown', async () => {
    const component = new ChromedashTypeahead();

    const candidate1 = {name: 'term=', doc: 'Some term'};
    assert.isFalse(component.shouldShowCandidate(candidate1, null));
    assert.isTrue(component.shouldShowCandidate(candidate1, ''));
    assert.isTrue(component.shouldShowCandidate(candidate1, 'te'));
    assert.isTrue(component.shouldShowCandidate(candidate1, 'term='));
    assert.isTrue(component.shouldShowCandidate(candidate1, 'Som'));
    assert.isFalse(component.shouldShowCandidate(candidate1, 'other'));
    assert.isFalse(component.shouldShowCandidate(candidate1, 'erm'));
    assert.isFalse(component.shouldShowCandidate(candidate1, 'erm'));

    assert.isTrue(component.shouldShowCandidate(candidate1, 'TERM='));
    assert.isTrue(component.shouldShowCandidate(candidate1, 'SOM'));

    const candidate2 = {name: 'path.dot.term=', doc: 'Some term'};
    assert.isTrue(component.shouldShowCandidate(candidate2, ''));
    assert.isTrue(component.shouldShowCandidate(candidate2, 'do'));
    assert.isTrue(component.shouldShowCandidate(candidate2, 'Ter'));
    assert.isTrue(component.shouldShowCandidate(candidate2, 'path.dot.'));
    assert.isFalse(component.shouldShowCandidate(candidate2, 'th'));
    assert.isFalse(component.shouldShowCandidate(candidate2, 'th.dot'));
  });
});

describe('chromedash-typeahead-dropdown', () => {
  it('can get, set, and clear its current item', async () => {
    const component = await fixture(html`
      <chromedash-typeahead-dropdown>
        <sl-input slot="trigger"> </sl-input>
        <sl-menu>
          <chromedash-typeahead-item
            id="item0"
            value="aaa"
            doc="Docs about aaa"
          ></chromedash-typeahead-item>
          <chromedash-typeahead-item
            id="item1"
            value="bbb"
            doc="Docs about bbb"
          ></chromedash-typeahead-item>
        </sl-menu>
      </chromedash-typeahead-dropdown>
    `);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTypeaheadDropdown);
    const item0 = component.querySelector('#item0');
    const item1 = component.querySelector('#item1');

    assert.equal(item0, component.getCurrentItem());

    component.setCurrentItem(item1);
    assert.equal(item1, component.getCurrentItem());

    component.resetSelection();
    assert.equal(null, component.getCurrentItem());
  });
});

describe('chromedash-typeahead-item', () => {
  it('renders a value and doc string', async () => {
    const component = await fixture(html`
      <chromedash-typeahead-item
        value="aValue"
        doc="Docs about it"
      ></chromedash-typeahead-item>
    `);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTypeaheadItem);
    assert.equal(component.getAttribute('role'), 'menuitem');

    const div = component.shadowRoot.querySelector('div');
    assert.exists(div);

    const divInnerHTML = div.innerHTML;
    assert.include(divInnerHTML, 'aValue');
    assert.include(divInnerHTML, 'Docs about it');
    assert.notInclude(divInnerHTML, 'active');
  });

  it('renders as active when sl-menu makes it current', async () => {
    const component = await fixture(html`
      <chromedash-typeahead-item
        value="aValue"
        doc="Docs about it"
        tabindex="0"
      ></chromedash-typeahead-item>
    `);
    const div = component.shadowRoot.querySelector('div');

    assert.include([...div.classList], 'active');
  });

  it('renders with the prefix in bold', async () => {
    const component = await fixture(html`
      <chromedash-typeahead-item
        value="aValue"
        doc="Docs about it"
        prefix="aVal"
      ></chromedash-typeahead-item>
    `);
    const valueEl = component.shadowRoot.querySelector('#value');
    assert.include(valueEl.innerHTML, 'aVal');
    assert.include(valueEl.innerHTML, 'ue');
    const bold = component.shadowRoot.querySelector('b');
    assert.include(bold.innerHTML, 'aVal');
    const docEl = component.shadowRoot.querySelector('#doc');
    assert.include(docEl.innerHTML, 'Docs about it');
  });

  it('matches any word in value or doc', async () => {
    const component = await fixture(html`
      <chromedash-typeahead-item
        value="a-search-keyword-search="
        doc="Search within keyword"
        prefix="sEar"
      ></chromedash-typeahead-item>
    `);
    const valueEl = component.shadowRoot.querySelector('#value');
    assert.include(valueEl.innerHTML, 'a-');
    assert.include(valueEl.innerHTML, 'sear');
    assert.include(valueEl.innerHTML, 'ch-keyword-search');
    const vBold = valueEl.querySelector('b');
    assert.include(vBold.innerHTML, 'sear');
    const docEl = component.shadowRoot.querySelector('#doc');
    assert.include(docEl.innerHTML, 'Sear');
    assert.include(docEl.innerHTML, 'ch within keyword');
    const dBold = docEl.querySelector('b');
    assert.include(dBold.innerHTML, 'Sear');
  });
});
