import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashReviewStatusIcon} from './chromedash-review-status-icon';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';
import {
  GATE_TYPES,
  GATE_PREPARING,
  VOTE_OPTIONS,
  VOTE_NA_SELF,
} from './form-field-enums';

const COMPONENT_HTML = html` <chromedash-review-status-icon
  featureId="12345"
  version="123"
  shippingType="Origin trial"
></chromedash-review-status-icon>`;

const GATE_WRONG_MILESTONE = {
  id: 12345001,
  earliest_milestone: 999, // non-matching.
  gate_type: GATE_TYPES['API_ORIGIN_TRIAL'],
};

const GATE_WRONG_TYPE = {
  id: 12345002,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['API_PLAN'], // non-matching.
};

const GATE_API_PREPARING = {
  id: 12345001,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['API_ORIGIN_TRIAL'],
  state: GATE_PREPARING,
};

const GATE_PRIVACY_PREPARING = {
  id: 12345002,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['PRIVACY_ORIGIN_TRIAL'],
  state: GATE_PREPARING,
};

const GATE_SECURITY_PREPARING = {
  id: 12345002,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['SECURITY_ORIGIN_TRIAL'],
  state: GATE_PREPARING,
};

const GATE_SECURITY_DENIED = {
  id: 12345002,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['SECURITY_ORIGIN_TRIAL'],
  state: VOTE_OPTIONS['DENIED'][0],
};

const GATE_API_STARTED = {
  id: 12345001,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['API_ORIGIN_TRIAL'],
  state: VOTE_OPTIONS['REVIEW_STARTED'][0],
};

const GATE_API_NEEDS_WORK = {
  id: 12345001,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['API_ORIGIN_TRIAL'],
  state: VOTE_OPTIONS['NEEDS_WORK'][0],
};

const GATE_API_APPROVED = {
  id: 12345001,
  earliest_milestone: 123,
  gate_type: GATE_TYPES['API_ORIGIN_TRIAL'],
  state: VOTE_OPTIONS['APPROVED'][0],
};

describe('chromedash-review-status-icon', () => {
  let getGatesStub: sinon.SinonStub;
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getGatesStub = sinon.stub(window.csClient, 'getGates');
  });

  afterEach(() => {
    getGatesStub.restore();
  });

  it('renders blank with no data', async () => {
    getGatesStub.returns(Promise.resolve({gates: []}));
    const component = await fixture(
      html`<chromedash-review-status-icon></chromedash-review-status-icon>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), null);
  });

  it('renders blank for a feature with no gates', async () => {
    getGatesStub.returns(Promise.resolve({gates: []}));
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), null);
  });

  it('is blank for a feature with no relevant gates', async () => {
    getGatesStub.returns(
      Promise.resolve({gates: [GATE_WRONG_MILESTONE, GATE_WRONG_TYPE]})
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), null);
  });

  it('renders an arrow for a feature with gates all PREPARING', async () => {
    getGatesStub.returns(
      Promise.resolve({gates: [GATE_API_PREPARING, GATE_PRIVACY_PREPARING]})
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'arrow_circle_right_20px');
  });

  it('renders "..." for a feature with any gates in progress', async () => {
    getGatesStub.returns(
      Promise.resolve({
        gates: [
          GATE_API_STARTED,
          GATE_SECURITY_PREPARING,
          GATE_PRIVACY_PREPARING,
        ],
      })
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'pending_20px');
  });

  it('renders "..." for a feature with mixed gates', async () => {
    getGatesStub.returns(
      Promise.resolve({
        gates: [
          GATE_API_APPROVED,
          GATE_SECURITY_PREPARING,
          GATE_PRIVACY_PREPARING,
        ],
      })
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'pending_20px');
  });

  it('renders "needs work" for a feature with a N-W gate', async () => {
    getGatesStub.returns(
      Promise.resolve({
        gates: [
          GATE_API_NEEDS_WORK,
          GATE_SECURITY_PREPARING,
          GATE_PRIVACY_PREPARING,
        ],
      })
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'autorenew_20px');
  });

  it('renders "approved" when all gates are approved', async () => {
    getGatesStub.returns(Promise.resolve({gates: [GATE_API_APPROVED]}));
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'check_circle_20px');
  });

  it('renders "denied" if any gate is denied', async () => {
    getGatesStub.returns(
      Promise.resolve({
        gates: [
          GATE_API_APPROVED,
          GATE_SECURITY_DENIED,
          GATE_PRIVACY_PREPARING,
        ],
      })
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'block_20px');
  });
});
