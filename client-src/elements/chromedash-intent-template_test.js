import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashIntentTemplate} from './chromedash-intent-template';

describe('chromedash-intent-template', () => {

  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        subject="A fake subject"
        intentBody="<div>A basic intent body</div>"
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    const body = component.shadowRoot.querySelector('#email-body-content');

    assert.equal(body.innerText, 'A basic intent body');
    assert.equal(subject.innerText, 'A fake subject');
  });
});
