import {html} from 'lit';
import SlCheckbox from '@shoelace-style/shoelace/dist/components/checkbox/checkbox.js';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashTextarea} from './chromedash-textarea';

describe('chromedash-textarea', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-textarea></chromedash-textarea>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashTextarea);
    const textareaElement = component.renderRoot.querySelector('textarea');
    assert.exists(textareaElement);
  });

  // Since ChromedashTextarea extends SlTextarea, this is a variation of the tests of
  // constraint validation used by shoelace in:
  //   https://github.com/shoelace-style/shoelace/blob/next/src/components/textarea/textarea.test.ts
  describe('when using constraint validation', () => {
    it('should be valid by default', async () => {
      const el = await fixture<ChromedashTextarea>(html`
        <chromedash-textarea></chromedash-textarea>
      `);
      assert.exists(el);
      await el.updateComplete;
      assert.equal(el.checkValidity(), true);
    });

    it('should be invalid when required and empty', async () => {
      const el = await fixture<ChromedashTextarea>(html`
        <chromedash-textarea required></chromedash-textarea>
      `);
      assert.exists(el);
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });

    it('should be invalid when required and after removing disabled ', async () => {
      const el = await fixture<ChromedashTextarea>(html`
        <chromedash-textarea disabled required></chromedash-textarea>
      `);
      assert.exists(el);
      el.disabled = false;
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });

    it('should be invalid when required and disabled is removed', async () => {
      const el = await fixture<ChromedashTextarea>(html`
        <chromedash-textarea disabled required></chromedash-textarea>
      `);
      assert.exists(el);
      el.disabled = false;
      await el.updateComplete;
      assert.equal(el.checkValidity(), false);
    });
  });

  describe('when using custom validation', () => {
    it('should be valid with multiple valid inputs', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          multiple
          chromedash_split_pattern="\\s+"
          chromedash_single_pattern="[a-z]+"
          value="abc def"
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), true);
    });

    it('should be valid with multiple valid inputs and extra whitespace', async () => {
      // Test with extra whitespace
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          multiple
          chromedash_split_pattern="\\s+"
          chromedash_single_pattern="[a-z]+"
          value="
  abc
 def
 "
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), true);
    });

    it('should be invalid with any invalid inputs', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          multiple
          chromedash_split_pattern="\\s+"
          chromedash_single_pattern="[a-z]+"
          value="abc123 def"
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), false);
    });

    it('should be invalid with any invalid inputs and extra whitespace', async () => {
      // Test with extra whitespace
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          multiple
          chromedash_split_pattern="\\s+"
          chromedash_single_pattern="[a-z]+"
          value="
  abc
 def 456
 "
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      assert.equal(component.checkValidity(), false);
    });
  });

  describe('when considering markdown support', () => {
    it('does not offer markdown if not specified', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      const useMarkdownEl = component.renderRoot.querySelector('#use-markdown');
      assert.notExists(useMarkdownEl);
      const showPreviewEl = component.renderRoot.querySelector('#show-preview');
      assert.notExists(showPreviewEl);
      const previewEl = component.renderRoot.querySelector('#preview');
      assert.notExists(previewEl);
    });

    it('offer markdown when specified', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea offermarkdown></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      const useMarkdownEl = component.renderRoot.querySelector('#use-markdown');
      assert.exists(useMarkdownEl);
      assert.notInclude(useMarkdownEl.outerHTML, 'checked');
      const showPreviewEl = component.renderRoot.querySelector('#show-preview');
      assert.notExists(showPreviewEl);
      const previewEl = component.renderRoot.querySelector('#preview');
      assert.notExists(previewEl);
    });

    it('check the box for markdown when in use', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          offermarkdown
          ismarkdown
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      const useMarkdownEl = component.renderRoot.querySelector('#use-markdown');
      assert.exists(useMarkdownEl);
      assert.include(useMarkdownEl.outerHTML, 'checked');
      const showPreviewEl = component.renderRoot.querySelector('#show-preview');
      assert.exists(showPreviewEl);
      assert.notInclude(showPreviewEl.outerHTML, 'checked');
      const previewEl = component.renderRoot.querySelector('#preview');
      assert.notExists(previewEl);
    });

    it('show the preview when checked', async () => {
      const component = await fixture<ChromedashTextarea>(
        html`<chromedash-textarea
          value="This is some **markdown**"
          offermarkdown
          ismarkdown
          .showPreview=${true}
        ></chromedash-textarea>`
      );
      assert.exists(component);
      await component.updateComplete;
      const useMarkdownEl = component.renderRoot.querySelector('#use-markdown');
      assert.exists(useMarkdownEl);
      assert.include(useMarkdownEl.outerHTML, 'checked');
      const showPreviewEl =
        component.renderRoot.querySelector<SlCheckbox>('#show-preview');
      assert.exists(showPreviewEl);
      assert.include(showPreviewEl.outerHTML, 'checked');
      const previewEl = component.renderRoot.querySelector('#preview');
      assert.exists(previewEl);
      const boldWord =
        component.renderRoot.querySelector<HTMLElement>('#preview strong');
      assert.exists(boldWord);
      assert.equal(boldWord.innerText, 'markdown');
    });
  });
});
