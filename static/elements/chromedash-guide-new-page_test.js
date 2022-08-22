import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideNewPage} from './chromedash-guide-new-page';

describe('chromedash-guide-new-page', () => {
  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-guide-new-page></chromedash-guide-new-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideNewPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // Process and UI feedback link is clickable
    assert.include(subheaderDiv.innerHTML, 'href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"');

    // overview form exists and is with action path
    const overviewForm = component.shadowRoot.querySelector('form[name="overview_form"]');
    assert.include(overviewForm.outerHTML, 'action="/guide/new"');

    // feature type chromedash-form-field exists and is with four options
    const featureTypeFormField = component.shadowRoot.querySelector(
      'chromedash-form-field[name="feature_type_radio_group"]');
    assert.include(featureTypeFormField.outerHTML, 'New feature incubation');
    assert.include(featureTypeFormField.outerHTML, 'Existing feature implementation');
    assert.include(featureTypeFormField.outerHTML, 'Web developer-facing change to existing code');
    assert.include(featureTypeFormField.outerHTML, 'Feature deprecation');

    // submit button exists
    const submitButton = component.shadowRoot.querySelector('input[type="submit"]');
    assert.exists(submitButton);
  });
});
