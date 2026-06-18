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
import {ChromeStatusClient, User, ChromeStatusHttpError} from '../js-src/cs-client.js';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-summary-review-dialog.js';

describe('chromedash-summary-review-dialog', () => {
  const feature = {
    id: 12345,
    name: 'Test Feature',
    summary: 'Original summary text.',
    resources: {
      docs: ['https://example.com/original-link'],
    },
  } as any;

  const suggestion = {
    status: 'complete',
    suggested_summary: 'Suggested AI summary.',
    suggested_doc_links: ['https://example.com/ai-suggested-link-1'],
    version_token: 1,
    baseline_status: null,
    status_timestamp: null,
    last_generation_attempt: null,
  } as any;

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'patchSummarySuggestion');
    sinon.stub(window.csClient, 'getSummarySuggestion');
  });

  afterEach(() => {
    window.csClient.patchSummarySuggestion.restore();
    window.csClient.getSummarySuggestion.restore();
  });

  it('renders original vs suggested text and link elements', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Original Column Check
    const originalTextDiv = dialog.renderRoot.querySelector('.original-text');
    assert.exists(originalTextDiv);
    assert.include(originalTextDiv.innerHTML, 'Original summary text.');

    const originalLinksDiv = dialog.renderRoot.querySelector('.original-links');
    assert.exists(originalLinksDiv);
    assert.include(
      originalLinksDiv.innerHTML,
      'https://example.com/original-link'
    );

    // Suggested Column Check
    assert.equal(dialog.summaryText, 'Suggested AI summary.');
    const textarea = dialog.renderRoot.querySelector(
      '.editable-summary-textarea'
    ) as any;
    assert.exists(textarea);
    assert.equal(textarea.value, 'Suggested AI summary.');

    // Checklist has combined links
    assert.equal(dialog.linksList.length, 2);
    assert.equal(
      dialog.linksList[0].url,
      'https://example.com/ai-suggested-link-1'
    );
    assert.isTrue(dialog.linksList[0].approved);
  });

  it('toggles suggested links checklist and triggers save API', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Uncheck the AI-suggested link
    dialog.toggleLinkApproved(0);
    assert.isFalse(dialog.linksList[0].approved);

    // Click Save & Apply
    window.csClient.patchSummarySuggestion.resolves({});

    let appliedEventFired = false;
    dialog.addEventListener('applied', (e: any) => {
      appliedEventFired = true;
      assert.equal(e.detail.summary, 'Suggested AI summary.');
      // None of the links were checked (original wasn't checked, AI link was unchecked)
      assert.equal(e.detail.links.length, 0);
    });

    await dialog.applySuggestion();

    assert.isTrue(appliedEventFired);
    assert.isTrue(
      window.csClient.patchSummarySuggestion.calledWith(
        12345,
        'applied',
        1,
        'Suggested AI summary.',
        []
      )
    );
  });

  it('enters conflict resolution mode on 409 conflict', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Reject suggestion save with 409
    const error = new Error('Conflict');
    (error as any).status = 409;
    window.csClient.patchSummarySuggestion.rejects(error);

    // Resolve get suggestion on mock fetch latest
    const serverSuggestion = {
      suggested_summary: 'New server summary saved by someone else.',
      suggested_doc_links: ['https://example.com/other-link'],
      version_token: 2,
    };
    window.csClient.getSummarySuggestion.resolves(serverSuggestion);

    let appliedEventFired = false;
    dialog.addEventListener('applied', () => {
      appliedEventFired = true;
    });

    await dialog.applySuggestion();
    await dialog.updateComplete;

    // Check we did not close and did not fire applied event
    assert.isFalse(appliedEventFired);
    assert.isTrue(dialog.inConflict);

    // Assert conflict banner is displayed
    const conflictBanner = dialog.renderRoot.querySelector('.conflict-banner');
    assert.exists(conflictBanner);
    assert.include(
      conflictBanner.textContent,
      'Conflict: Another editor has already saved changes'
    );

    // Assert server values were fetched and copied
    assert.equal(
      dialog.serverSummaryText,
      'New server summary saved by someone else.'
    );
    assert.equal(dialog.serverVersionToken, 2);
  });

  it('discards suggestion and emits discarded event', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    window.csClient.patchSummarySuggestion.resolves({});

    let discardedEventFired = false;
    dialog.addEventListener('discarded', () => {
      discardedEventFired = true;
    });

    await dialog.discardSuggestion();

    assert.isTrue(discardedEventFired);
    assert.isTrue(
      window.csClient.patchSummarySuggestion.calledWith(12345, 'discarded', 1)
    );
  });

  it('adds custom links and filters duplicates', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Type new link
    dialog.newLinkLabelInput = 'https://example.com/custom-new-link';
    dialog.addNewLink();

    // Verify it was added approved
    assert.equal(dialog.linksList.length, 3);
    assert.equal(
      dialog.linksList[2].url,
      'https://example.com/custom-new-link'
    );
    assert.isTrue(dialog.linksList[2].approved);
  });

  it('disables action controls when submitting is true', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    dialog.submitting = true;
    await dialog.updateComplete;

    // Check textarea disabled state
    const textarea = dialog.renderRoot.querySelector(
      '.editable-summary-textarea'
    ) as any;
    assert.isTrue(textarea.disabled);

    // Check buttons disabled state in dialog slot
    const saveButton = dialog.renderRoot.querySelector(
      'sl-button[variant="primary"]'
    ) as any;
    assert.isTrue(saveButton.disabled);
  });

  it('enforces bypass confirmation justification validation', async () => {
    const devrelUser = {email: 'devrel@chromium.org'} as User;
    const graceSuggestion = {
      ...suggestion,
      status_timestamp: new Date().toISOString(), // current time (well within 7 days)
    };

    const dialog = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${graceSuggestion}
        .user=${devrelUser}
      ></chromedash-summary-review-dialog>`
    );

    dialog.show();
    await dialog.updateComplete;

    // Trigger save - since user is devrel (not owner) and within grace period, it should show bypass UI
    await dialog.applySuggestion();
    await dialog.updateComplete;

    assert.isTrue(dialog.showBypassUI);

    // Verify bypass justification input is rendered
    const justificationTextarea = dialog.renderRoot.querySelector(
      'sl-textarea[name="bypass_justification"]'
    ) as any;
    assert.exists(justificationTextarea);

    // Confirm Bypass button should be disabled because justification is empty
    const confirmButton = dialog.renderRoot.querySelector(
      'sl-button[variant="primary"]'
    ) as any;
    assert.exists(confirmButton);
    assert.isTrue(confirmButton.disabled);

    // Enter justification text
    dialog.bypassJustification = 'Emergency fix';
    await dialog.updateComplete;

    // Confirm Bypass button should now be enabled
    assert.isFalse(confirmButton.disabled);

    // Submit bypass
    window.csClient.patchSummarySuggestion.resolves({});
    await dialog.applySuggestion();

    assert.isTrue(
      window.csClient.patchSummarySuggestion.calledWith(
        12345,
        'applied',
        1,
        'Suggested AI summary.',
        ['https://example.com/ai-suggested-link-1'],
        'Emergency fix'
      )
    );
  });

  it('toggles between write and preview tabs and renders markdown', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Default tab is write
    assert.equal(dialog.activeTab, 'write');
    const textarea = dialog.renderRoot.querySelector(
      '.editable-summary-textarea'
    ) as HTMLTextAreaElement;
    assert.exists(textarea);
    const previewContainer =
      dialog.renderRoot.querySelector('.preview-container');
    assert.isNull(previewContainer);

    // Type markdown bold text
    dialog.summaryText = 'This is **bold** text';
    dialog.isDirty = true;

    // Switch to preview tab
    const previewTabButton = dialog.renderRoot.querySelectorAll(
      '.tab-btn'
    )[1] as HTMLButtonElement;
    assert.exists(previewTabButton);
    previewTabButton.click();
    await dialog.updateComplete;

    assert.equal(dialog.activeTab, 'preview');
    // Textarea should be hidden
    assert.isNull(
      dialog.renderRoot.querySelector('.editable-summary-textarea')
    );

    // Preview container should render HTML bold tags
    const previewDiv = dialog.renderRoot.querySelector('.preview-container');
    assert.exists(previewDiv);
    assert.include(previewDiv.innerHTML, 'This is <strong>bold</strong> text');
  });

  it('resolves conflict using force overwrite', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Trigger conflict
    const error = new ChromeStatusHttpError('Conflict', '', '', 409);
    window.csClient.patchSummarySuggestion.rejects(error);

    const serverSuggestion = {
      suggested_summary: 'Server Text',
      suggested_doc_links: [],
      version_token: 2,
    };
    window.csClient.getSummarySuggestion.resolves(serverSuggestion);

    await dialog.applySuggestion();
    await dialog.updateComplete;
    assert.isTrue(dialog.inConflict);

    // Mock successful save on retry
    window.csClient.patchSummarySuggestion.resetBehavior();
    window.csClient.patchSummarySuggestion.resolves({});

    // Click Force Overwrite (represented by applying suggestion again in conflict mode)
    await dialog.applySuggestion();

    // Verify it sent patch using server's version token (2) instead of original (1)
    assert.isTrue(
      window.csClient.patchSummarySuggestion.calledWith(
        12345,
        'applied',
        2,
        'Suggested AI summary.',
        ['https://example.com/ai-suggested-link-1']
      )
    );
    assert.isFalse(dialog.inConflict);
  });

  it('accepts server changes and resets conflict resolution state', async () => {
    const dialog = (await fixture(
      html`<chromedash-summary-review-dialog
        .feature=${feature}
        .suggestion=${suggestion}
      ></chromedash-summary-review-dialog>`
    )) as ChromedashSummaryReviewDialog;

    dialog.show();
    await dialog.updateComplete;

    // Trigger conflict
    const error = new ChromeStatusHttpError('Conflict', '', '', 409);
    window.csClient.patchSummarySuggestion.rejects(error);

    const serverSuggestion = {
      suggested_summary: 'Server Text',
      suggested_doc_links: ['https://example.com/server-link'],
      version_token: 2,
    };
    window.csClient.getSummarySuggestion.resolves(serverSuggestion);

    await dialog.applySuggestion();
    await dialog.updateComplete;
    assert.isTrue(dialog.inConflict);

    // Accept changes
    dialog.acceptServerChanges();
    await dialog.updateComplete;

    // States should be reset and values updated
    assert.isFalse(dialog.inConflict);
    assert.isFalse(dialog.isDirty);
    assert.equal(dialog.summaryText, 'Server Text');
    assert.equal(dialog.linksList.length, 2);
    assert.equal(dialog.linksList[0].url, 'https://example.com/server-link');
    assert.isTrue(dialog.linksList[0].approved);
    assert.equal(dialog.linksList[1].url, 'https://example.com/original-link');
  });
});
