import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashIntentTemplate} from './chromedash-intent-template';

describe('chromedash-intent-template', () => {
  const validFeature = {
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    feature_type_int: 0,
    new_crbug_url: 'fake crbug link',
    owner_emails: ['owner1@example.com', 'owner2@example.com'],
    explainer_links: [
      'https://example.com/explainer1',
      'https://example.com/explainer2',
    ],
    blink_components: ['Blink'],
    interop_compat_risks: 'Some risks here',
    ongoing_constraints: 'Some constraints',
    finch_name: 'AFinchName',
    browsers: {
      chrome: {
        status: {
          milestone_str: 'No active development',
          text: 'No active development',
          val: 1,
        },
      },
      ff: {view: {text: 'No signal', val: 5}},
      safari: {view: {text: 'No signal', val: 5}},
      webdev: {view: {text: 'Positive', val: 1}},
      other: {view: {}},
    },
    stages: [
      {
        id: 1,
        stage_type: 110,
        intent_stage: 1,
      },
      {
        id: 2,
        stage_type: 150,
        intent_thread_url: 'https://example.com/experiment',
        desktop_first: 100,
        desktop_last: 106,
        android_first: 100,
        android_last: 106,
        webview_first: 100,
        webview_last: 106,
        extensions: [
          {
            id: 22,
            stage_type: 151,
            intent_thread_url: 'https://example.com/extend',
            desktop_last: 109,
          },
        ],
      },
      {
        id: 3,
        stage_type: 160,
        intent_thread_url: 'https://example.com/ship',
        desktop_first: 110,
        android_first: 110,
        webview_first: 110,
      },
      {
        id: 4,
        stage_type: 160,
      },
    ],
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {
          milestone_str: 'No active development',
          text: 'No active development',
          val: 1,
        },
      },
      ff: {view: {text: 'No signal', val: 5}},
      safari: {view: {text: 'No signal', val: 5}},
      webdev: {view: {text: 'No signal', val: 4}},
      other: {view: {}},
    },
    resources: {
      samples: ['fake sample link one', 'fake sample link two'],
      docs: ['fake doc link one', 'fake doc link two'],
    },
    standards: {
      maturity: {
        short_text: 'Incubation',
        text: 'Specification being incubated in a Community Group',
        val: 3,
      },
      status: {text: "Editor's Draft", val: 4},
    },
    tags: ['tag_one'],
  };
  const validGate = {
    id: 200,
    stage_id: 2,
    gate_type: 2,
  };

  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[1]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    const body = component.shadowRoot.querySelector('#email-body-content');
    const expectedBody = `Contact emails
owner1@example.com, owner2@example.com


Explainer
https://example.com/explainer1
https://example.com/explainer2


Specification
None


Design docs
fake doc link one
fake doc link two


Summary

fake detailed summary




Blink component
Blink


Search tags
tag_one


TAG review
None


Risks



Interoperability and Compatibility

Some risks here



Gecko: No signal

WebKit: No signal

Web developers: No signal

Other signals:


WebView application risks

Does this intent deprecate or change behavior of existing APIs, such that it has potentially high risk for Android WebView-based applications?

None




Goals for experimentation

None




Ongoing technical constraints
Some constraints


Debuggability

None




Will this feature be supported on all six Blink platforms (Windows, Mac, Linux, ChromeOS, Android, and Android WebView)?
No



Is this feature fully tested by web-platform-tests?
No


Flag name on chrome://flags
None


Finch feature name
AFinchName


Non-finch justification
None


Requires code in //chrome?
No


Estimated milestones
Shipping on desktop	110
Origin trial desktop first	100
Origin trial desktop last	106
Origin trial extension end milestone	109
Shipping on Android	110
Origin trial Android first	100
Origin trial Android last	106
Shipping on WebView	110
Origin trial WebView first	100
Origin trial WebView last	106



Link to entry on Chrome Status Test
http://localhost:8000/feature/123456?gate=200


Links to previous Intent discussions
Intent to Experiment: https://example.com/experiment
Intent to Extend Experiment: https://example.com/extend
Intent to Ship: https://example.com/ship



This intent message was generated by Chrome Status Test.`;

    const expectedSubject = 'Intent to Experiment: feature one';
    assert.equal(body.innerText, expectedBody);
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders deprecation plan intent', async () => {
    // Deprecation feature type.
    validFeature.feature_type_int = 3;
    // Deprecation plan gate type.
    validGate.gate_type = 5;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Intent to Deprecate and Remove: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders prototype intent', async () => {
    // New feature type.
    validFeature.feature_type_int = 0;
    // Prototype gate type.
    validGate.gate_type = 1;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Intent to Prototype: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders "Ready for Developer Testing" template', async () => {
    // New feature type.
    validFeature.feature_type_int = 0;
    // No gate or stage provided for DevTrial templates.
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Ready for Developer Testing: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders "Intent to Ship" template', async () => {
    // New feature type.
    validFeature.feature_type_int = 0;
    // Ship gate type.
    validGate.gate_type = 4;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Intent to Ship: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders "Intent to Extend Experiment" template', async () => {
    // New feature type.
    validFeature.feature_type_int = 0;
    // OT extension gate type.
    validGate.gate_type = 3;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[1].extensions[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Intent to Extend Experiment: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders "Request for Deprecation Trial" template', async () => {
    // Deprecation feature type.
    validFeature.feature_type_int = 3;
    // OT gate type.
    validGate.gate_type = 2;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[1].extensions[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Request for Deprecation Trial: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders "Intent to Extend Deprecation Trial" template', async () => {
    // Deprecation feature type.
    validFeature.feature_type_int = 3;
    // OT extension gate type.
    validGate.gate_type = 3;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[1].extensions[0]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Intent to Extend Deprecation Trial: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });

  it('renders PSA shipping template', async () => {
    // PSA feature type.
    validFeature.feature_type_int = 2;
    // Shipping gate type.
    validGate.gate_type = 4;
    const component = await fixture(
      html`<chromedash-intent-template
        appTitle="Chrome Status Test"
        .feature=${validFeature}
        .stage=${validFeature.stages[2]}
        .gate=${validGate}
      >
      </chromedash-intent-template>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentTemplate);

    const expectedSubject = 'Web-Facing Change PSA: feature one';
    const subject = component.shadowRoot.querySelector(
      '#email-subject-content'
    );
    assert.equal(subject.innerText, expectedSubject);
  });
});
