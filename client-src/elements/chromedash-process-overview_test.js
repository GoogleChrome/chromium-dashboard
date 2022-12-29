import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashProcessOverview} from './chromedash-process-overview';

describe('chromedash-proces-overview', () => {
  let process; let feature;

  beforeEach(() => {
    process = {
      stages: [{
        name: 'stage one',
        description: 'a description',
        progress_items: [],
        outgoing_stage: 1,
        actions: [],
        stage_type: 110,
      }],
    };
    feature = {
      id: 123456,
      intent_stage_int: 1,
      active_stage_id: 1,
      stages: [
        {
          id: 1,
          stage_type: 110,
          intent_stage: 1,
        },
        {
          id: 2,
          stage_type: 120,
          intent_stage: 2,
        },
      ],
    };
  });

  it('renders with basic data', async () => {
    const component = await fixture(
      html`<chromedash-process-overview
              .process=${process}
              .feature=${feature}
           ></chromedash-process-overview>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashProcessOverview);
    const stageHeader = component.shadowRoot.querySelector('th');
    assert.exists(stageHeader);
  });

  it('highlights the active stage', async () => {
    const component = await fixture(
      html`<chromedash-process-overview
              .process=${process}
              .feature=${feature}
             ></chromedash-process-overview>`);
    assert.exists(component);

    const activeRow = component.shadowRoot.querySelector('tr.active');
    assert.exists(activeRow);
    assert.include(activeRow.innerHTML, 'stage one');
  });

  it('does not highlight when there is no active stage', async () => {
    feature.active_stage_id = null;
    const component = await fixture(
      html`<chromedash-process-overview
              .process=${process}
              .feature=${feature}
             ></chromedash-process-overview>`);
    assert.exists(component);

    const activeRow = component.shadowRoot.querySelector('tr.active');
    assert.isNull(activeRow);
  });
});
