import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashMyFeaturesPage} from './chromedash-myfeatures-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-myfeatures-page', () => {
  let recentReview; let pendingReview; let featureIOwn; let featureIStarred;

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
    sinon.stub(window.csClient, 'getStars');
    window.csClient.getStars.returns(Promise.resolve([123456]));

    // For the child component - chromedash-feature-table
    sinon.stub(window.csClient, 'searchFeatures');
    window.csClient.searchFeatures.returns(Promise.resolve([]));

    recentReview = null;
    pendingReview = null;
    featureIOwn = null;
    featureIStarred = null;
  });

  afterEach(() => {
    window.csClient.getPermissions.restore();
    window.csClient.getStars.restore();
  });

  it('user has no approval permission', async () => {
    window.csClient.getPermissions.returns(Promise.resolve({
      can_approve: false,
      can_create_feature: true,
      can_edit: true,
      is_admin: false,
      email: 'example@gmail.com',
    }));
    const component = await fixture(
      html`<chromedash-myfeatures-page></chromedash-myfeatures-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashMyFeaturesPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'My features');

    const slDetails = component.shadowRoot.querySelectorAll('sl-details');
    slDetails.forEach((item) => {
      const itemHTML = item.outerHTML;
      if (itemHTML.includes('summary="Features I own"')) featureIOwn = item;
      if (itemHTML.includes('summary="Features I starred"')) featureIStarred = item;
      if (itemHTML.includes('summary="Features pending my approval"')) pendingReview = item;
      if (itemHTML.includes('summary="Recently reviewed features"')) recentReview = item;
    });

    // No review-related sl-details
    assert.notExists(pendingReview);
    assert.notExists(recentReview);

    // Features I own sl-details exists and has a correct query
    assert.exists(featureIOwn);
    assert.include(featureIOwn.innerHTML, 'query="owner:me"');

    // Features I starred sl-details exists and has a correct query
    assert.exists(featureIStarred);
    assert.include(featureIStarred.innerHTML, 'query="starred-by:me"');
  });

  it('user has approval permission', async () => {
    window.csClient.getPermissions.returns(Promise.resolve({
      can_approve: true,
      can_create_feature: true,
      can_edit: true,
      is_admin: false,
      email: 'example@gmail.com',
    }));
    const component = await fixture(
      html`<chromedash-myfeatures-page></chromedash-myfeatures-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashMyFeaturesPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, 'My features');

    const slDetails = component.shadowRoot.querySelectorAll('sl-details');
    slDetails.forEach((item) => {
      const itemHTML = item.outerHTML;
      if (itemHTML.includes('summary="Features I own"')) featureIOwn = item;
      if (itemHTML.includes('summary="Features I starred"')) featureIStarred = item;
      if (itemHTML.includes('summary="Features pending my approval"')) pendingReview = item;
      if (itemHTML.includes('summary="Recently reviewed features"')) recentReview = item;
    });

    // "Recently reviewed features" exists and has a correct query
    assert.exists(pendingReview);
    assert.include(pendingReview.innerHTML, 'query="pending-approval-by:me"');

    // "Features pending my approval" exists and has a correct query
    assert.exists(recentReview);
    assert.include(recentReview.innerHTML, 'query="is:recently-reviewed"');

    // "Features I own" sl-details exists and has a correct query
    assert.exists(featureIOwn);
    assert.include(featureIOwn.innerHTML, 'query="owner:me"');

    // "Features I starred" sl-details exists and has a correct query
    assert.exists(featureIStarred);
    assert.include(featureIStarred.innerHTML, 'query="starred-by:me"');
  });
});
