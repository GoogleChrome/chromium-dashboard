import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFeaturePage} from './chromedash-feature-page';

describe('chromedash-feature-page', () => {
  let feature;

  beforeEach(() => {
    feature = {
      id: 123456,
      resources: {
        samples: ['fake sample link one', 'fake sample link two'],
        docs: ['fake doc link one', 'fake doc link two'],
      },
      standards: {
        spec: 'fake spec link',
      },
      tags: ['tag_one'],
    };
  });

  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-feature-page></chromedash-feature-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeaturePage);
    const featureDiv = component.shadowRoot.querySelector('div#feature');
    assert.exists(featureDiv);
  });

  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-feature-page
              .feature=${feature}
             ></chromedash-feature-page>`);
    assert.exists(component);

    const sampleSection = component.shadowRoot.querySelector('section#demo');
    assert.exists(sampleSection);
    assert.include(sampleSection.innerHTML, 'href="fake sample link one"');
    assert.include(sampleSection.innerHTML, 'href="fake sample link two"');

    const docSection = component.shadowRoot.querySelector('section#documentation');
    assert.exists(docSection);
    assert.include(docSection.innerHTML, 'href="fake doc link one"');
    assert.include(docSection.innerHTML, 'href="fake doc link two"');

    const specSection = component.shadowRoot.querySelector('section#specification');
    assert.exists(specSection);
    assert.include(specSection.innerHTML, 'href="fake spec link"');

    const tagSection = component.shadowRoot.querySelector('section#tags');
    assert.exists(tagSection);
    assert.include(tagSection.innerHTML, 'href="/features#tags:tag_one"');
  });
});
