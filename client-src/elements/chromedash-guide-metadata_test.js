import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideMetadata} from './chromedash-guide-metadata';

describe('chromedash-guide-metadata', () => {
  const feature = {
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    enterprise_feature_categories: [1, 2],
    feature_type: 'fake feature type',
    intent_stage: 'fake intent stage',
    new_crbug_url: 'fake crbug link',
    cc_recipients: ['fake chrome cc one', 'fake chrome cc two'],
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {text: 'fake chrome status text'},
        devrel: ['devrel1@example.com', 'devrel2@example.com'],
      },
      ff: {view: {text: 'fake ff view text'}},
      safari: {view: {text: 'fake safari view text'}},
      webdev: {view: {text: 'fake webdev view text'}},
    },
    resources: {
      samples: ['fake sample link one', 'fake sample link two'],
      docs: ['fake doc link one', 'fake doc link two'],
    },
    standards: {
      spec: 'fake spec link',
      maturity: {text: 'Unknown standards status - check spec link for status'},
    },
    tags: ['tag_one'],
  };

  it('renders with fake data (user is not admin)', async () => {
    const component = await fixture(
      html`<chromedash-guide-metadata
             .feature=${feature}
             .isAdmin=${false}>
           </chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    const metadataDiv = component.shadowRoot.querySelector('div#metadata-readonly');
    assert.exists(metadataDiv);
    // edit button exists
    assert.include(metadataDiv.innerHTML, 'id="open-metadata"');
    // feature summary is listed
    assert.include(metadataDiv.innerHTML, 'fake detailed summary');
    // feature owners are listed
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner one"');
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner two"');
    // devrel recipients are listed
    assert.include(metadataDiv.innerHTML, 'href="mailto:devrel1@example.com"');
    assert.include(metadataDiv.innerHTML, 'href="mailto:devrel2@example.com"');
    // cc recipients are listed
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome cc one"');
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome cc two"');
    // feature category is listed
    assert.include(metadataDiv.innerHTML, 'fake category');
    // enterprise feature category are not listed
    assert.notInclude(metadataDiv.innerHTML, 'Security/Privacy');
    assert.notInclude(metadataDiv.innerHTML, 'User Productivity/Apps');
    // feature feature type is listed
    assert.include(metadataDiv.innerHTML, 'fake feature type');
    // feature intent stage is listed
    assert.include(metadataDiv.innerHTML, 'fake intent stage');
    // feature tag is listed
    assert.include(metadataDiv.innerHTML, 'tag_one');
    // feature status is listed
    assert.include(metadataDiv.innerHTML, 'fake chrome status text');
    // feature blink component is listed
    assert.include(metadataDiv.innerHTML, 'Blink');
    // delete button does not exists
    assert.notInclude(metadataDiv.innerHTML, 'class="delete-button"');
  });

  it('renders enterprise feature with fake data (user is not admin)', async () => {
    const enterpriseFeature = {...feature, is_enterprise_feature: true};
    const component = await fixture(
      html`<chromedash-guide-metadata
             .feature=${enterpriseFeature}
             .isAdmin=${false}>
           </chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    const metadataDiv = component.shadowRoot.querySelector('div#metadata-readonly');
    assert.exists(metadataDiv);
    // edit button exists
    assert.include(metadataDiv.innerHTML, 'id="open-metadata"');
    // feature summary is listed
    assert.include(metadataDiv.innerHTML, 'fake detailed summary');
    // feature owners are listed
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner one"');
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner two"');
    // devrel recipients are not listed
    assert.notInclude(metadataDiv.innerHTML, 'href="mailto:devrel1@example.com"');
    assert.notInclude(metadataDiv.innerHTML, 'href="mailto:devrel2@example.com"');
    // cc recipients are listed
    assert.notInclude(metadataDiv.innerHTML, 'href="mailto:fake chrome cc one"');
    assert.notInclude(metadataDiv.innerHTML, 'href="mailto:fake chrome cc two"');
    // feature category is not listed
    assert.notInclude(metadataDiv.innerHTML, 'fake category');
    // enterprise feature category are listed
    assert.include(metadataDiv.innerHTML, 'Security/Privacy');
    assert.include(metadataDiv.innerHTML, 'User Productivity/Apps');
    // feature feature type is listed
    assert.include(metadataDiv.innerHTML, 'fake feature type');
    // feature intent stage is listed
    assert.notInclude(metadataDiv.innerHTML, 'fake intent stage');
    // feature tag is listed
    assert.notInclude(metadataDiv.innerHTML, 'tag_one');
    // feature status is listed
    assert.notInclude(metadataDiv.innerHTML, 'fake chrome status text');
    // feature blink component is listed
    assert.include(metadataDiv.innerHTML, 'Blink');
    // delete button does not exists
    assert.notInclude(metadataDiv.innerHTML, 'class="delete-button"');
  });

  it('user is an admin', async () => {
    const component = await fixture(
      html`<chromedash-guide-metadata
             .feature=${feature}
             .isAdmin=${true}>
           </chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    const metadataDiv = component.shadowRoot.querySelector('div#metadata-readonly');
    assert.exists(metadataDiv);
    // delete button exists
    assert.include(metadataDiv.innerHTML, 'class="delete-button"');
  });
});
