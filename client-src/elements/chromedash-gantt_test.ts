import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import {ChromedashGantt} from './chromedash-gantt';

describe('chromedash-gantt', () => {
  const validFeature = {
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    intent_stage: 'fake intent stage',
    new_crbug_url: 'fake crbug link',
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {
          text: 'Enabled by default',
          val: 1,
        },
      },
      ff: {view: {text: 'No signal', val: 5}},
      safari: {view: {text: 'No signal', val: 5}},
      webdev: {view: {text: 'No signal', val: 4}},
      other: {view: {}},
    },
    stages: [
      {
        // Prototype stage.
        id: 1,
        stage_type: 110,
        intent_stage: 1,
        extensions: [],
      },
      {
        // Dev Trial stage.
        id: 2,
        stage_type: 130,
        desktop_first: 100,
        android_first: 101,
        intent_stage: 2,
        extensions: [],
      },
      {
        // Origin Trial stage 1.
        id: 3,
        stage_type: 150,
        intent_stage: 2,
        desktop_first: 100,
        desktop_last: 103,
        android_first: 100,
        android_last: 103,
        extensions: [],
      },
      {
        // Origin Trial stage 2.
        id: 3,
        stage_type: 150,
        intent_stage: 2,
        desktop_first: 104,
        desktop_last: 106,
        android_first: 104,
        android_last: 106,
        webview_first: 104,
        webview_last: 106,
        extensions: [
          {
            id: 31,
            stage_type: 151,
            intent_stage: 11,
            desktop_last: 108,
            extensions: [],
          },
        ],
      },
      {
        // Ship stage.
        id: 2,
        stage_type: 160,
        intent_stage: 2,
        extensions: [],
        desktop_first: 109,
        android_first: 110,
        ios_first: 110,
        webview_first: 109,
      },
    ],
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

  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-gantt></chromedash-gantt>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGantt);
  });

  it('renders with valid feature data', async () => {
    const component: ChromedashGantt = await fixture(
      html` <chromedash-gantt .feature=${validFeature}></chromedash-gantt>`
    );
    assert.exists(component);
    await component.updateComplete;
    const desktopChart = component.renderRoot.querySelector('#desktop-chart');
    assert.include(desktopChart?.innerHTML, 'Dev Trial: 100');
    assert.include(desktopChart?.innerHTML, 'Origin Trial: 100 to 103');
    assert.include(desktopChart?.innerHTML, 'Origin Trial: 104 to 108');
    assert.include(desktopChart?.innerHTML, 'Shipping: 109');

    const androidChart = component.renderRoot.querySelector('#android-chart');
    assert.include(androidChart?.innerHTML, 'Dev Trial: 101');
    assert.include(androidChart?.innerHTML, 'Origin Trial: 100 to 103');
    assert.include(androidChart?.innerHTML, 'Origin Trial: 104 to 108');
    assert.include(androidChart?.innerHTML, 'Shipping: 110');

    const iOSChart = component.renderRoot.querySelector('#ios-chart');
    assert.include(iOSChart?.innerHTML, 'Shipping: 110');
    assert.notInclude(iOSChart?.innerHTML, 'Dev Trial');
    assert.notInclude(iOSChart?.innerHTML, 'Origin Trial');

    const webViewChart = component.renderRoot.querySelector('#webview-chart');
    assert.include(webViewChart?.innerHTML, 'Shipping: 109');
    assert.include(webViewChart?.innerHTML, 'Origin Trial: 104 to 108');
    assert.notInclude(webViewChart?.innerHTML, 'Dev Trial');
    assert.notInclude(webViewChart?.innerHTML, 'Origin Trial: 100 to 103');
  });
});
