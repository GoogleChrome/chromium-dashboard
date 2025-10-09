import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashReviewStatusIcon} from './chromedash-review-status-icon';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';
import {
  GATE_PREPARING,
  VOTE_OPTIONS,
  VOTE_NA_SELF,
  FEATURE_TYPES,
} from './form-field-enums';

const FEATURE = {
  id: 5347893,
  roadmap_stage_ids: [57463],
  feature_type_int: 0, // Not a PSA feature
};

const FEATURE_PSA = {
  id: 5347894,
  roadmap_stage_ids: [57463],
  // This feature type should trigger the new conditional logic.
  feature_type_int: FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0],
};

const COMPONENT_HTML = html` <chromedash-review-status-icon
  .feature=${FEATURE}
></chromedash-review-status-icon>`;

const COMPONENT_HTML_PSA = html` <chromedash-review-status-icon
  .feature=${FEATURE_PSA}
></chromedash-review-status-icon>`;

const GATE_WRONG_STAGE = {
  id: 12345001,
  stage_id: 999, // non-matching.
};

const GATE_API_PREPARING = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'API Owners',
  state: GATE_PREPARING,
};

const GATE_PRIVACY_PREPARING = {
  id: 12345002,
  stage_id: 57463,
  state: GATE_PREPARING,
};

const GATE_SECURITY_PREPARING = {
  id: 12345002,
  stage_id: 57463,
  state: GATE_PREPARING,
};

const GATE_SECURITY_DENIED = {
  id: 12345002,
  stage_id: 57463,
  state: VOTE_OPTIONS['DENIED'][0],
};

const GATE_API_STARTED = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'API OWNERS',
  state: VOTE_OPTIONS['REVIEW_STARTED'][0],
};

const GATE_API_NEEDS_WORK = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'API OWNERS',
  state: VOTE_OPTIONS['NEEDS_WORK'][0],
};

const GATE_API_APPROVED = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'API OWNERS',
  state: VOTE_OPTIONS['APPROVED'][0],
};

const GATE_SECURITY_NA = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'Security',
  state: VOTE_OPTIONS['NA'][0],
};

const GATE_PRIVACY_NA_SELF = {
  id: 12345001,
  stage_id: 57463,
  team_name: 'Privacy',
  state: VOTE_NA_SELF,
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
    getGatesStub.returns(Promise.resolve({gates: [GATE_WRONG_STAGE]}));
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
    getGatesStub.returns(
      Promise.resolve({
        gates: [GATE_API_APPROVED, GATE_PRIVACY_NA_SELF, GATE_SECURITY_NA],
      })
    );
    const component = await fixture(COMPONENT_HTML);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(icon.getAttribute('name'), 'check_circle_filled_20px');
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

  it('renders "approved" for a PSA feature even if gates are not started', async () => {
    getGatesStub.returns(
      Promise.resolve({gates: [GATE_API_PREPARING, GATE_PRIVACY_PREPARING]})
    );
    const component = await fixture(COMPONENT_HTML_PSA);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReviewStatusIcon);
    const icon = component.shadowRoot!.querySelector('sl-icon');
    assert.exists(icon);
    assert.equal(
      icon.getAttribute('name'),
      'check_circle_filled_20px',
      'PSA feature should be approved by default'
    );
    // Check that there is no link, because targetGateId is set to undefined.
    const link = component.shadowRoot!.querySelector('a');
    assert.isNull(link, 'should not have a link for PSA features');
  });
});
