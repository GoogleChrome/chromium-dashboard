/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {ChromedashReleaseNotesPage} from './chromedash-releases-page.js';
import {TaskStatus} from '@lit/task';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-releases-page.js';
import './chromedash-summary-review-dialog.js';

describe('chromedash-release-notes-page', () => {
  const channelsPromise = Promise.resolve({
    stable: {version: 125},
    beta: {version: 126},
    dev: {version: 127},
  });

  const featuresPromise = Promise.resolve({
    'Enabled by default': [
      {
        id: 12345,
        name: 'Mock Feature One',
        summary: 'This is a mock description for feature one.',
        blink_components: ['Blink>HTML'],
        resources: {
          docs: ['https://example.com/original-doc'],
        },
      },
    ],
  });

  const suggestionPromise = Promise.resolve({
    status: 'complete',
    suggested_summary: 'AI suggested summary text.',
    suggested_doc_links: ['https://example.com/ai-suggested-link'],
    version_token: 1,
    summary_provenance: null,
    doc_links_provenance: null,
  });

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);

    sinon.stub(window.csClient, 'getChannels').returns(channelsPromise);
    sinon
      .stub(window.csClient, 'getFeaturesInMilestone')
      .returns(featuresPromise);
    sinon
      .stub(window.csClient, 'getSummarySuggestion')
      .returns(suggestionPromise);
    sinon.stub(window.csClient, 'triggerSummaryGeneration').resolves({});
    sinon.stub(window.csClient, 'patchSummarySuggestion').resolves({});
  });

  afterEach(() => {
    window.csClient.getChannels.restore();
    window.csClient.getFeaturesInMilestone.restore();
    window.csClient.getSummarySuggestion.restore();
    window.csClient.triggerSummaryGeneration.restore();
    window.csClient.patchSummarySuggestion.restore();
  });

  async function waitForStatusTask(statusEl: any, expectedCanReview = true) {
    await statusEl.updateComplete;
    if (expectedCanReview) {
      // Wait for cascading properties to flow down (shadowRoot becomes populated)
      while (
        !statusEl.shadowRoot ||
        statusEl.shadowRoot.innerHTML.trim() === '<!---->'
      ) {
        await new Promise(resolve => setTimeout(resolve, 10));
        await statusEl.updateComplete;
      }

      // Wait for async task to resolve (skeleton loader disappears)
      while (statusEl.shadowRoot.querySelector('sl-skeleton')) {
        await new Promise(resolve => setTimeout(resolve, 10));
        await statusEl.updateComplete;
      }
    }
  }

  async function waitForLoading(component: ChromedashReleaseNotesPage) {
    while (component.loading) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    while (component._featuresTask.status === TaskStatus.PENDING) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    await component.updateComplete;
    const cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    ) as any[];
    await Promise.all(cards.map(card => card.updateComplete));

    const statusEls = cards
      .map(card =>
        card.renderRoot.querySelector('chromedash-feature-suggestion-status')
      )
      .filter(Boolean) as any[];

    const canReview = !!(
      component.user?.can_review_release_notes || component.user?.is_admin
    );

    if (canReview && statusEls.length === 0) {
      throw new Error(
        `TEST BUG: statusEls is empty! cards count: ${cards.length}, component.user: ${JSON.stringify(
          component.user
        )}`
      );
    }

    await Promise.all(statusEls.map(el => waitForStatusTask(el, canReview)));
  }

  it('renders features list to normal users without editor control panel', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };
    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);
    assert.exists(component);
    assert.instanceOf(component, ChromedashReleaseNotesPage);

    // Should load milestone search input
    const input = component.renderRoot.querySelector('.milestone-search-input') as HTMLInputElement;
    assert.exists(input);
    assert.equal(input.value, '125');

    // Should render feature details
    const card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    const cardContent = card.renderRoot.querySelector('.feature-card');
    assert.exists(cardContent);
    assert.include(cardContent.innerHTML, 'Mock Feature One');
    assert.include(
      cardContent.innerHTML,
      'This is a mock description for feature one.'
    );

    // Control panel should NOT be visible to normal user
    const statusEl = card.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    assert.exists(statusEl);
    await statusEl.updateComplete;
    const controlPanel = statusEl.shadowRoot.querySelector(
      '.suggestion-control-panel'
    );
    assert.isNull(controlPanel);
  });

  it('renders suggestion controls and opens review dialog for editors', async () => {
    const user = {
      can_create_feature: true,
      can_edit: true,
      is_admin: true,
      can_review_release_notes: true,
      email: 'editor@google.com',
    };
    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);
    assert.exists(component);

    const card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    const statusEl = card.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    assert.exists(statusEl);
    await statusEl.updateComplete;
    const controlPanel = statusEl.shadowRoot.querySelector(
      '.suggestion-control-panel'
    );
    assert.exists(controlPanel);
    assert.include(controlPanel.innerHTML, 'Draft Available');

    const reviewButton = statusEl.shadowRoot.querySelector(
      'sl-button[variant="primary"]'
    ) as any;
    assert.exists(reviewButton);
    assert.include(reviewButton.innerText, 'Review 2 suggestions');

    // Click "Review Suggestion" and check if it opens active state
    reviewButton.click();
    await component.updateComplete;

    const dialog = component.renderRoot.querySelector(
      '#review-dialog'
    ) as ChromedashSummaryReviewDialog;
    assert.exists(dialog);
    await dialog.updateComplete;

    assert.equal(component.activeReviewFeature?.id, 12345);
    assert.equal(dialog.summaryText, 'AI suggested summary text.');

    // Checklist has combined links
    assert.equal(dialog.linksList.length, 2);
    assert.equal(
      dialog.linksList[0].url,
      'https://example.com/ai-suggested-link'
    );
    assert.isTrue(dialog.linksList[0].approved);
    assert.equal(dialog.linksList[1].url, 'https://example.com/original-doc');
    assert.isFalse(dialog.linksList[1].approved);
  });

  it('renders various suggestion tag states', async () => {
    const user = {
      can_create_feature: true,
      can_edit: true,
      is_admin: true,
      can_review_release_notes: true,
      email: 'editor@google.com',
    };

    // 1. in_progress
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      suggested_summary: null,
      suggested_doc_links: [],
      version_token: 1,
    });
    let component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);
    let card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    let statusEl = card.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    assert.exists(statusEl);
    await statusEl.updateComplete;
    let controlPanel = statusEl.shadowRoot.querySelector(
      '.suggestion-control-panel'
    );
    assert.exists(controlPanel);
    const progressEl = controlPanel.querySelector(
      'chromedash-ai-summary-progress'
    );
    assert.exists(progressEl);
    await progressEl.updateComplete;
    const tag = progressEl.shadowRoot.querySelector('sl-tag');
    assert.exists(tag);
    assert.include(tag.textContent, 'Generating');
    // Verify the Generate button does not exist (it should be hidden when in_progress)
    const generateBtn = controlPanel.querySelector('sl-button');
    assert.isNull(generateBtn);

    // 2. applied
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'applied',
      suggested_summary: 'Applied summary.',
      suggested_doc_links: [],
      version_token: 1,
    });
    component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);
    card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    statusEl = card.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    assert.exists(statusEl);
    await statusEl.updateComplete;
    controlPanel = statusEl.shadowRoot.querySelector(
      '.suggestion-control-panel'
    );
    assert.include(controlPanel!.innerHTML, 'Applied');
    assert.include(controlPanel!.innerHTML, 'Edit applied summary');

    // 3. failed
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'failed',
      suggested_summary: null,
      suggested_doc_links: [],
      version_token: 1,
    });
    component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);
    card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    statusEl = card.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    assert.exists(statusEl);
    await statusEl.updateComplete;
    controlPanel = statusEl.shadowRoot.querySelector(
      '.suggestion-control-panel'
    );
    assert.include(controlPanel!.innerHTML, 'Failed');
    assert.include(controlPanel!.innerHTML, 'Generate Summary'); // Retry button
  });

  it('renders WebDX Baseline status badges', async () => {
    const user = {
      can_create_feature: true,
      can_edit: true,
      is_admin: true,
      can_review_release_notes: true,
      email: 'editor@google.com',
    };

    // Mock widely baseline status
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'applied',
      suggested_summary: 'AI summary',
      suggested_doc_links: [],
      version_token: 1,
      baseline_status: 'widely',
    });

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    const badge = card.renderRoot.querySelector('sl-tag[variant="success"]');
    assert.exists(badge);
    assert.include(badge.innerHTML, 'Baseline Widely Available');

    // Verify official SVG image is rendered inside the badge
    const img = badge.querySelector('img');
    assert.exists(img);
    assert.equal(
      img.getAttribute('src'),
      '/static/img/baseline-widely-icon.svg'
    );
  });

  it('handles features without summary text and missing links gracefully', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };

    // Mock feature with empty summary and missing docs
    window.csClient.getFeaturesInMilestone.restore();
    sinon.stub(window.csClient, 'getFeaturesInMilestone').resolves({
      'Enabled by default': [
        {
          id: 99999,
          name: 'Empty Feature',
          summary: '',
          blink_components: ['Blink'],
          resources: {docs: [], samples: []},
        },
      ],
    });

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const card = component.renderRoot.querySelector(
      'chromedash-release-feature-card'
    ) as any;
    assert.exists(card);
    const featureSummary = card.renderRoot.querySelector('.feature-summary');
    assert.exists(featureSummary);
    assert.include(featureSummary.innerHTML, 'No summary provided.');

    assert.notInclude(card.renderRoot.innerHTML, 'Documentation links:');
  });

  it('receives applied event from review dialog and updates local state', async () => {
    const user = {
      can_create_feature: true,
      can_edit: true,
      is_admin: true,
      can_review_release_notes: true,
      email: 'editor@google.com',
    };

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const dialog = component.renderRoot.querySelector(
      '#review-dialog'
    ) as ChromedashSummaryReviewDialog;
    assert.exists(dialog);

    component.activeReviewFeature =
      component._featuresTask.value!['Enabled by default'][0];

    // Dispatch custom event simulated from dialog
    dialog.dispatchEvent(
      new CustomEvent('applied', {
        detail: {
          summary: 'Newly updated summary text!',
          links: ['https://example.com/newly-approved'],
        },
      })
    );

    assert.equal(
      component.activeReviewFeature!.summary,
      'Newly updated summary text!'
    );
    assert.equal(
      component.activeReviewFeature!.resources!.docs[0],
      'https://example.com/newly-approved'
    );
  });

  it('renders milestone channel status banner correctly', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };

    // Override channels stub to return stable/beta/dev versions
    window.csClient.getChannels.restore();
    sinon.stub(window.csClient, 'getChannels').resolves({
      stable: {version: 125},
      beta: {version: 126},
      dev: {version: 127},
    });

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    // Default milestone is stable (125)
    let banner = component.renderRoot.querySelector('sl-alert');
    assert.exists(banner);
    assert.include(
      banner.innerHTML,
      'Chrome 125 is now available on the Stable channel.'
    );

    // Navigate/switch to Beta (126)
    component.selectedMilestone = 126;
    await component.updateComplete;
    banner = component.renderRoot.querySelector('sl-alert');
    assert.exists(banner);
    assert.include(banner.innerHTML, 'Chrome 126 is currently in Beta.');

    // Navigate/switch to Dev (127)
    component.selectedMilestone = 127;
    await component.updateComplete;
    banner = component.renderRoot.querySelector('sl-alert');
    assert.exists(banner);
    assert.include(
      banner.innerHTML,
      'Chrome 127 is currently on the Dev channel'
    );
  });

  it('renders DCC fallback warning banner for older milestones', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };

    window.csClient.getChannels.restore();
    sinon.stub(window.csClient, 'getChannels').resolves({
      stable: {version: 125},
      beta: {version: 126},
      dev: {version: 127},
    });

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    // Select a milestone older than stable - 5 (125 - 5 = 120, select 110)
    component.selectedMilestone = 110;
    await component.updateComplete;

    const banner = component.renderRoot.querySelector('.dcc-redirect-banner');
    assert.exists(banner);
    assert.include(
      banner.textContent,
      'Official editorial release notes for Chrome 110 are hosted on the Chrome Developer Blog.'
    );

    const link = banner!.querySelector('sl-button');
    assert.exists(link);
    assert.equal(
      link.getAttribute('href'),
      'https://developer.chrome.com/release-notes/110'
    );
  });

  it('filters milestone combobox options on user text input and handles selection', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };
    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const input = component.renderRoot.querySelector('.milestone-search-input') as HTMLInputElement;
    assert.exists(input);

    // 1. Initially, dropdown options are hidden
    let optionsContainer = component.renderRoot.querySelector('.milestone-options-dropdown');
    assert.isNull(optionsContainer);

    // 2. Focus input -> dropdown options should appear
    input.dispatchEvent(new Event('focus'));
    await component.updateComplete;

    optionsContainer = component.renderRoot.querySelector('.milestone-options-dropdown');
    assert.exists(optionsContainer);

    const initialOptionsCount = optionsContainer.querySelectorAll('.milestone-option').length;
    // Should have a large set of milestone options in our scalable list
    assert.isAbove(initialOptionsCount, 100);

    // 3. Type text '12' -> should filter options containing '12'
    input.value = '12';
    input.dispatchEvent(new Event('input'));
    await component.updateComplete;

    const filteredOptions = optionsContainer.querySelectorAll('.milestone-option');
    filteredOptions.forEach((option: any) => {
      assert.include(option.textContent, '12');
    });

    // 4. Click option '120' -> should set input value and trigger fetch
    const option120 = Array.from(filteredOptions).find((opt: any) => opt.textContent.includes('120')) as HTMLElement;
    assert.exists(option120);

    const getFeaturesStub = window.csClient.getFeaturesInMilestone as sinon.SinonStub;
    getFeaturesStub.resetHistory();
    option120.click();
    await waitForLoading(component);

    const inputAfter = component.renderRoot.querySelector('.milestone-search-input') as HTMLInputElement;
    assert.exists(inputAfter);
    assert.equal(inputAfter.value, '120');
    assert.isTrue(getFeaturesStub.calledWith(120));

    // Dropdown options should hide after selection
    assert.isNull(component.renderRoot.querySelector('.milestone-options-dropdown'));
  });

  it('displays error message inside combobox dropdown when no milestone matches search query', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };
    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const input = component.renderRoot.querySelector('.milestone-search-input') as HTMLInputElement;
    assert.exists(input);

    input.dispatchEvent(new Event('focus'));
    await component.updateComplete;

    // Type a bad milestone number
    input.value = '999';
    input.dispatchEvent(new Event('input'));
    await component.updateComplete;

    const optionsContainer = component.renderRoot.querySelector('.milestone-options-dropdown');
    assert.exists(optionsContainer);

    const noResults = optionsContainer.querySelector('.dropdown-no-results');
    assert.exists(noResults);
    assert.include(noResults.textContent, 'No milestone "999" found.');
    assert.include(noResults.textContent, 'Valid milestones: 1 to');
  });

  it('renders channel quick-jump buttons and navigates milestone on click', async () => {
    const user = {
      can_create_feature: false,
      can_edit: false,
      is_admin: false,
      can_review_release_notes: false,
      email: 'user@example.com',
    };

    window.csClient.getChannels.restore();
    sinon.stub(window.csClient, 'getChannels').resolves({
      stable: {version: 125},
      beta: {version: 126},
      dev: {version: 127},
    });

    const component = (await fixture(
      html`<chromedash-release-notes-page .user=${user}></chromedash-release-notes-page>`
    )) as ChromedashReleaseNotesPage;
    await waitForLoading(component);

    const quickJumps = component.renderRoot.querySelector('.channel-quick-jumps');
    assert.exists(quickJumps);

    const buttons = quickJumps.querySelectorAll('sl-button');
    assert.equal(buttons.length, 3);
    assert.include(buttons[0].textContent, 'Stable: 125');
    assert.include(buttons[1].textContent, 'Beta: 126');
    assert.include(buttons[2].textContent, 'Dev: 127');

    // Click on Beta: 126 and verify it navigates and fetches
    const getFeaturesStub = window.csClient.getFeaturesInMilestone as sinon.SinonStub;
    getFeaturesStub.resetHistory();

    const betaBtn = buttons[1] as HTMLElement;
    betaBtn.click();
    await waitForLoading(component);

    assert.equal(component.selectedMilestone, 126);
    assert.isTrue(getFeaturesStub.calledWith(126));
  });
});
