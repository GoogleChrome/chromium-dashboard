import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashIntentContent} from './chromedash-intent-content';

describe('chromedash-intent-content', () => {
  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-intent-content
        appTitle="Chrome Status Test"
        subject="A fake subject"
        intentBody="<div>A basic intent body</div>"
      >
      </chromedash-intent-content>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentContent);

    const subject = component.renderRoot.querySelector(
      '#email-subject-content'
    ) as HTMLElement;
    const body = component.renderRoot.querySelector(
      '#email-body-content'
    ) as HTMLElement;

    assert.equal(body.innerText, 'A basic intent body');
    assert.equal(subject.innerText, 'A fake subject');
  });
});
