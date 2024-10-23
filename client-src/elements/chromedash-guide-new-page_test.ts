import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideNewPage} from './chromedash-guide-new-page';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-new-page', () => {
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getBlinkComponents');
    window.csClient.getBlinkComponents.returns(Promise.resolve({}));
  });

  afterEach(() => {
    window.csClient.getBlinkComponents.restore();
  });

  it('renders with fake data', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture(
      html`<chromedash-guide-new-page .userEmail=${userEmail}>
      </chromedash-guide-new-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideNewPage);

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // Process and UI feedback link is clickable
    assert.include(
      subheaderDiv.innerHTML,
      'href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"'
    );

    // overview form exists and is with action path
    const overviewForm = component.renderRoot.querySelector(
      'form[name="overview_form"]'
    )!;
    assert.include(overviewForm.outerHTML, 'action="/guide/new"');

    // owner field filled with the user email
    assert.include(overviewForm.innerHTML, userEmail);

    // feature type chromedash-form-field exists and is with four options
    const featureTypeFormField = component.renderRoot.querySelector(
      'chromedash-form-field[name="feature_type_radio_group"]'
    )!;
    assert.include(featureTypeFormField.outerHTML, 'New or changed feature');
    assert.include(featureTypeFormField.outerHTML, 'Chromium catches up');
    assert.include(
      featureTypeFormField.outerHTML,
      'No developer-visible change'
    );
    assert.include(featureTypeFormField.outerHTML, 'Feature removal');

    // submit button exists
    const submitButton = component.renderRoot.querySelector(
      'input[type="submit"]'
    );
    assert.exists(submitButton);
  });
});
