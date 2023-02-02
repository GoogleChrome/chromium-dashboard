import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashTextarea} from './chromedash-textarea';

describe('chromedash-textarea', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-textarea></chromedash-textarea>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTextarea);
    const textareaElement = component.shadowRoot.querySelector('textarea');
    assert.exists(textareaElement);
  });

  // Since ChromedashTextarea extends SlTextarea, this is a variation of the tests of
  // constraint validation used by shoelace in:
  //   https://github.com/shoelace-style/shoelace/blob/next/src/components/textarea/textarea.test.ts
  describe('when using constraint validation', () => {
    it('should be valid by default', async () => {
      const el = await fixture(html` <chromedash-textarea></chromedash-textarea> `);
      assert.exists(el);
      await el.updateComplete;
      assert.equal(el.checkValidity(), true);
    });

    it('should be invalid when required and empty', async () => {
      const el = await fixture(html` <chromedash-textarea required></chromedash-textarea> `);
      assert.exists(el);
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });

    it('should be invalid when required and after removing disabled ', async () => {
      const el = await fixture(html` <chromedash-textarea disabled required></chromedash-textarea> `);
      assert.exists(el);
      el.disabled = false;
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });

    it('should be invalid when required and disabled is removed', async () => {
      const el = await fixture(html` <chromedash-textarea disabled required></chromedash-textarea> `);
      assert.exists(el);
      el.disabled = false;
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });
  });

  describe('when using custom validation', () => {
    it('should be valid with multiple valid inputs', async () => {
      const component = await fixture(
        html`<chromedash-textarea multiple
                chromedash_split_pattern="\\\s+"
                chromedash_single_pattern="[a-z]+"
                value="abc def"></chromedash-textarea>`);
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), true);
    });

    it('should be valid with multiple valid inputs and extra whitespace', async () => {
      // Test with extra whitespace
      const component = await fixture(
        html`<chromedash-textarea multiple
                chromedash_split_pattern="\\\s+"
                chromedash_single_pattern="[a-z]+"
                value=" \n  abc  \n def \n "></chromedash-textarea>`);
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), true);
    });

    it('should be invalid with any invalid inputs', async () => {
      const component = await fixture(
        html`<chromedash-textarea multiple
                chromedash_split_pattern="\\\s+"
                chromedash_single_pattern="[a-z]+"
                value="abc123 def"></chromedash-textarea>`);
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), false);
    });

    it('should be invalid with any invalid inputs and extra whitespace', async () => {
      // Test with extra whitespace
      const component = await fixture(
        html`<chromedash-textarea multiple
                chromedash_split_pattern="\\\s+"
                chromedash_single_pattern="[a-z]+"
                value=" \n  abc  \n def 456 \n "></chromedash-textarea>`);
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), false);
    });
  });
});
