import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashMyFeaturesPage} from './chromedash-myfeatures-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-myfeatures-page', () => {
  let recentReview;
  let pendingReview;
  let featureICanEdit;
  let featureIStarred;

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getStars');
    window.csClient.getStars.returns(Promise.resolve([123456]));

    // For the child component - chromedash-feature-table
    sinon.stub(window.csClient, 'searchFeatures');
    window.csClient.searchFeatures.returns(Promise.resolve({features: []}));

    recentReview = null;
    pendingReview = null;
    featureICanEdit = null;
    featureIStarred = null;
  });

  afterEach(() => {
    window.csClient.getStars.restore();
  });

  it('user has no approval permission', async () => {
    const user = {
      can_create_feature: true,
      can_edit_all: true,
      is_admin: false,
      email: 'example@gmail.com',
      editable_features: [],
    };
    const component = await fixture(
      html`<chromedash-myfeatures-page .user=${user}>
      </chromedash-myfeatures-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashMyFeaturesPage);

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'My features');

    const slDetails = component.renderRoot.querySelectorAll('sl-details');
    slDetails.forEach(item => {
      const itemHTML = item.outerHTML;
      if (itemHTML.includes('summary="Features I can edit"'))
        featureICanEdit = item;
      if (itemHTML.includes('summary="Features I starred"'))
        featureIStarred = item;
      if (itemHTML.includes('summary="Features pending my approval"'))
        pendingReview = item;
      if (itemHTML.includes('summary="Recently reviewed features"'))
        recentReview = item;
    });

    // No review-related sl-details
    assert.notExists(pendingReview);
    assert.notExists(recentReview);

    // "Features I can edit" sl-details exists and has a correct query
    assert.exists(featureICanEdit);
    assert.include(featureICanEdit.innerHTML, 'query="can_edit:me"');
    assert.include(featureICanEdit.innerHTML, 'showenterprise');

    // Features I starred sl-details exists and has a correct query
    assert.exists(featureIStarred);
    assert.include(featureIStarred.innerHTML, 'query="starred-by:me"');
    assert.include(featureIStarred.innerHTML, 'showenterprise');
  });

  it('user has approval permission', async () => {
    const user = {
      approvable_gate_types: [54],
      can_create_feature: true,
      can_edit_all: true,
      is_admin: false,
      email: 'example@gmail.com',
      editable_features: [],
    };
    const component = await fixture(
      html`<chromedash-myfeatures-page .user=${user}>
      </chromedash-myfeatures-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashMyFeaturesPage);

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'My features');

    const slDetails = component.renderRoot.querySelectorAll('sl-details');
    slDetails.forEach(item => {
      const itemHTML = item.outerHTML;
      if (itemHTML.includes('summary="Features I can edit'))
        featureICanEdit = item;
      if (itemHTML.includes('summary="Features I starred"'))
        featureIStarred = item;
      if (itemHTML.includes('summary="Features pending my approval"'))
        pendingReview = item;
      if (itemHTML.includes('summary="Recently reviewed features"'))
        recentReview = item;
    });

    // "Recently reviewed features" exists and has a correct query
    assert.exists(pendingReview);
    assert.include(pendingReview.innerHTML, 'query="pending-approval-by:me"');
    assert.include(pendingReview.innerHTML, 'showenterprise');

    // "Features pending my approval" exists and has a correct query
    assert.exists(recentReview);
    assert.include(recentReview.innerHTML, 'query="is:recently-reviewed"');
    assert.include(recentReview.innerHTML, 'showenterprise');

    // "Features I can edit" sl-details exists and has a correct query
    assert.exists(featureICanEdit);
    assert.include(featureICanEdit.innerHTML, 'query="can_edit:me"');
    assert.include(featureICanEdit.innerHTML, 'showenterprise');

    // "Features I starred" sl-details exists and has a correct query
    assert.exists(featureIStarred);
    assert.include(featureIStarred.innerHTML, 'query="starred-by:me"');
    assert.include(featureIStarred.innerHTML, 'showenterprise');
  });
});
