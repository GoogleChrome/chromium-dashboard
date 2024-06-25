import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashSettingsPage} from './chromedash-settings-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-settings-page', () => {
  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getSettings');
  });

  afterEach(() => {
    window.csClient.getSettings.restore();
  });

  it('user has not signed in and get user pref not found response', async () => {
    window.csClient.getSettings.returns(
      Promise.reject(new Error('User preference not found'))
    );
    const component = await fixture(
      html`<chromedash-settings-page></chromedash-settings-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashSettingsPage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(
      toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('user has notify_as_starrer value as true', async () => {
    window.csClient.getSettings.returns(
      Promise.resolve({notify_as_starrer: true})
    );
    const component = await fixture(
      html`<chromedash-settings-page></chromedash-settings-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashSettingsPage);

    // header exists
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'User preferences');

    // form exists and has a submit button
    const formEl = component.shadowRoot.querySelector('form');
    assert.exists(formEl);
    assert.include(formEl.innerHTML, 'input type="submit"');

    // checkbox exists and is checked
    const checkboxEl = component.shadowRoot.querySelector('sl-checkbox');
    assert.exists(checkboxEl);
    assert.include(checkboxEl.outerHTML, 'checked');
  });

  it('user has notify_as_starrer value as false', async () => {
    window.csClient.getSettings.returns(
      Promise.resolve({notify_as_starrer: false})
    );
    const component = await fixture(
      html`<chromedash-settings-page></chromedash-settings-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashSettingsPage);

    // header exists
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'User preferences');

    // form exists and has a submit button
    const formEl = component.shadowRoot.querySelector('form');
    assert.exists(formEl);
    assert.include(formEl.innerHTML, 'input type="submit"');

    // checkbox exists and is not checked
    const checkboxEl = component.shadowRoot.querySelector('sl-checkbox');
    assert.exists(checkboxEl);
    assert.notInclude(checkboxEl.outerHTML, 'checked');
  });
});

// When you get a chance, I'd like your insights into how to fix the "you have unsaved changes" logic for the user settings page.  Right now if the user changes then saves, then navigates away, they still get the warning.
// It looks like the logic in chromedash-app that waits 1 sec then checks of the user is still on the same pageComponent (to detect a failed submission) is also being used here because the user settings component stays on the same component and just shows "settings save" as a toast.
