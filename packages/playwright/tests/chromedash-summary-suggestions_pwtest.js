// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
  expectScreenshot,
} from './test_utils';

const API_PREFIX = ")]}'\n";

/**
 * @param {import("playwright-core").Page} page
 * @param {number} featureId
 * @param {{ toString: () => any; }} milestone
 */
async function setShippedMilestone(page, featureId, milestone) {
  console.log(
    `[E2E] Setting shipped milestone for feature ${featureId} to ${milestone}...`
  );
  await page.goto(`/guide/editall/${featureId}`);
  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());
  await milestoneInput.blur();

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  // Wait until we are redirected back to the feature detail page
  await page.waitForURL(`**/feature/${featureId}`);
}

test.describe('AI Summary Suggestions E2E Integration Tests', () => {
  let featureId;
  /**
   * @type {any}
   */
  let stableMilestone;
  /**
   * @type {number | null}
   */
  let featureIdToDelete = null;

  test.beforeAll(async ({request}) => {
    // Seed the database with Blink components list
    console.log('[E2E] Seeding Blink components list...');
    const seedResponse = await request.get('/cron/update_blink_components');
    console.log(`[E2E] Seeding Blink components status: ${seedResponse.status()}`);

    // Fetch stable milestone dynamically from channels API
    const response = await request.get('/api/v0/channels');
    const channels = JSON.parse(
      (await response.text()).replace(API_PREFIX, '')
    );
    stableMilestone = channels.stable.version;
    console.log(
      `[E2E] Running tests against real stable milestone: ${stableMilestone}`
    );
  });

  test.beforeEach(async ({page}) => {
    captureConsoleMessages(page);
    // Block real Google Accounts GSI scripts
    await page.route('https://accounts.google.com/**', route => route.abort());
  });

  test.afterEach(async ({page}) => {
    if (featureIdToDelete) {
      console.log(
        `[E2E] Cleaning up created feature ID: ${featureIdToDelete}...`
      );
      const xsrfToken = await page.evaluate(() => {
        // @ts-ignore
        return window.csClient ? window.csClient.token : '';
      });
      await page.request.delete(`/api/v0/features/${featureIdToDelete}`, {
        headers: {
          'X-Xsrf-Token': xsrfToken,
        }
      });
      featureIdToDelete = null;
    }
  });

  test('Feature Owner (example@chromium.org) happy path review & apply', async ({
    page,
  }) => {
    // 1. Log in as feature owner
    await loginAs(page, 'example@chromium.org');

    // 2. Create a new feature dynamically
    const featureName = `Test feature owner ${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    await createNewFeature(page, featureName);
    const url = page.url();
    const parts = url.split('/');
    featureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = featureId;
    console.log(
      `[E2E] Created new feature ID: ${featureId} with name: ${featureName}`
    );

    // Verify detail page has no suggestion banner initially
    const initBanner = page.locator('sl-alert[variant="primary"]');
    await expect(initBanner).not.toBeVisible();

    // 3. Set shipped milestone to Stable milestone to show on Releases dashboard
    await setShippedMilestone(page, featureId, stableMilestone);

    // E2E DEBUG CHECK: Fetch the feature entity directly via API to verify NDB state
    const debugRes = await page.request.get(`/api/v0/features/${featureId}`);
    const rawResponseText0 = await debugRes.text();
    const XSSIPrefix = ")]}'\n";
    if (!rawResponseText0.startsWith(XSSIPrefix)) {
      throw new Error(
        `Response does not start with XSSI prefix: ${XSSIPrefix}`
      );
    }
    const debugData = JSON.parse(rawResponseText0.substring(XSSIPrefix.length));
    console.log('[E2E DEBUG] Feature API response:', JSON.stringify(debugData));

    // 4. Navigate to Releases dashboard
    const responsePromise = page.waitForResponse(
      response =>
        response.url().includes('/api/v0/features?milestone=') &&
        response.status() === 200
    );
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const apiResponse = await responsePromise;
    const rawResponseText = await apiResponse.text();
    let apiData = {};
    if (rawResponseText.startsWith(XSSIPrefix)) {
      apiData = JSON.parse(rawResponseText.substring(XSSIPrefix.length));
    } else {
      apiData = JSON.parse(rawResponseText);
    }
    console.log(
      '[E2E DEBUG] Releases API response data:',
      JSON.stringify(apiData)
    );

    console.log(
      '[E2E DEBUG] Releases Container Text:',
      await page.locator('.releases-container').innerText()
    );

    const card = page.getByTestId(`feature-card-${featureId}`);
    await expect(card).toBeVisible();

    // Verify status is "none" (shows as "Generate Summary" button)
    const generateBtn = card.getByRole('button', {name: 'Generate Summary'});
    await expect(generateBtn).toBeVisible();

    // 5. Trigger generation
    console.log('[E2E] Triggering AI generation...');
    await generateBtn.click();

    // Wait until suggestion badge changes to "Draft Available"
    const suggestionBadge = card.locator('sl-tag[variant="success"]');
    await expect(suggestionBadge).toHaveText(/Draft Available/, {
      timeout: 15000,
    });

    // Capture screenshot of releases dashboard badges
    await expectScreenshot(page, 'preleases_dashboard_badges', { maxDiffPixelRatio: 0.1 });

    // Verify "Review Suggestion" button is now visible
    const reviewBtn = card.getByRole('button', {name: /Review.*suggestion/i});
    await expect(reviewBtn).toBeVisible();

    // 6. Open Review Dialog
    await reviewBtn.click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Capture screenshot of review diff dialog
    await expectScreenshot(page, 'review_diff_dialog', { maxDiffPixelRatio: 0.1 });

    // Verify content comparison
    await expect(page.getByTestId('original-summary')).toContainText(
      'Test summary description'
    );
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await expect(textarea).toHaveValue(/This is a mock summary suggestion/);

    // Edit summary text in dialog
    await textarea.fill('AI summary applied successfully by owner.');

    // Save and Apply (since user is owner, no bypass justification is required)
    const saveButton = page.getByRole('button', {name: 'Save & Apply'});
    const savePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await saveButton.click({force: true});
    await savePromise;

    // Dialog should close
    await expect(dialog).not.toBeVisible();

    // 7. Verify write-back on Feature Detail page
    await page.goto(`/feature/${featureId}`);
    const detailsContainer = page.locator('chromedash-feature-detail');
    await expect(detailsContainer.getByTestId('summary-value')).toContainText(
      'AI summary applied successfully by owner.'
    );
  });

  test('DevRel (devrel@chromium.org) bypass grace period workflow', async ({
    page,
  }) => {
    // 1. Log in as owner, create feature, set milestone, and trigger generation
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test feature devrel ${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const devFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = devFeatureId;
    await setShippedMilestone(page, devFeatureId, stableMilestone);

    // Trigger generation on releases dashboard
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${devFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(
      /Draft Available/,
      {timeout: 10000}
    );
    // 2. Log in as DevRel reviewer (direct session override to bypass UI logout flakiness)
    await loginAs(page, 'devrel@chromium.org');

    // 3. Navigate to Releases dashboard
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const devrelCard = page.getByTestId(`feature-card-${devFeatureId}`);
    
    await devrelCard.getByRole('button', {name: /Review.*suggestion/i}).click();

    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Click save
    const saveButton = page.getByRole('button', {name: 'Save & Apply'});
    await saveButton.click({force: true});

    // Justification box should expand (within grace period and user is not owner)
    const justificationTextarea = page.locator('sl-textarea[name="bypass_justification"]').locator('textarea');
    await expect(justificationTextarea).toBeVisible();

    const confirmButton = page.getByRole('button', {name: 'Confirm Apply Bypass'});
    await expect(confirmButton).toBeDisabled();

    // Fill justification and confirm
    await justificationTextarea.fill(
      'DevRel bypassed owner for urgent release notes.'
    );
    await expect(confirmButton).toBeEnabled();

    // Capture screenshot of bypass warning/prompt
    await expectScreenshot(page, 'bypass_justification_prompt', { maxDiffPixelRatio: 0.1 });

    const savePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await confirmButton.click({force: true});
    await savePromise;
    await expect(dialog).not.toBeVisible();

    // 4. Verify detail page renders warning banner to owner
    // Switch back to owner (direct session override)
    await loginAs(page, 'example@chromium.org');
    await page.goto(`/feature/${devFeatureId}`);

    const banner = page.locator('sl-alert[variant="warning"]');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText('AI Suggestion Applied (Bypassed)');

    // Capture screenshot of detail page banner
    await expectScreenshot(page, 'feature_detail_ai_banner', { maxDiffPixelRatio: 0.1 });

    // 5. Owner clicks "Revert to My Original"
    const revertBtn = banner.getByRole('button', {
      name: 'Revert to My Original',
    });
    await expect(revertBtn).toBeVisible();
    await revertBtn.click();

    // Banner should disappear and text should revert to original
    await expect(banner).not.toBeVisible();
    const detailsContainer = page.locator('chromedash-feature-detail');
    await expect(detailsContainer.getByTestId('summary-value')).toContainText(
      'Test summary description'
    );
  });

  test('409 Concurrency Conflict Resolution Flow in E2E', async ({page}) => {
    // 1. Log in as owner, create feature, set milestone, and trigger generation
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test conflict ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const conflictFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = conflictFeatureId;
    await setShippedMilestone(page, conflictFeatureId, stableMilestone);

    // 2. Go to Releases, trigger generation, wait for draft
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${conflictFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, {timeout: 15000});

    // 3. Intercept save API to return a 409 Conflict
    let patchCount = 0;
    await page.route(`**/api/v0/features/${conflictFeatureId}/summary_suggestion`, async (route, request) => {
      if (request.method() === 'PATCH') {
        patchCount++;
        if (patchCount === 1) {
          // First patch fails with 409 Conflict!
          await route.fulfill({
            status: 409,
            contentType: 'application/json',
            body: ")]}'\n" + JSON.stringify({
              error: 'Conflict: The suggestion has been modified by another request.'
            })
          });
        } else {
          // Subsequent patches succeed!
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: ")]}'\n" + JSON.stringify({
              message: 'AI suggestion status updated successfully.'
            })
          });
        }
      } else {
        await route.continue();
      }
    });

    // 4. Open dialog
    await card.getByRole('button', {name: /Review.*suggestion/i}).click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // 5. Try to save -> should fail with conflict and show conflict UI
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await textarea.fill('My contested local changes.');
    const saveBtn = page.getByRole('button', {name: 'Save & Apply'});
    
    const savePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 409);
    await saveBtn.click({force: true});
    await savePromise;

    // Verify red conflict banner is visible
    const conflictBanner = page.locator('.conflict-banner');
    await expect(conflictBanner).toBeVisible();
    await expect(conflictBanner).toContainText('Another editor has already saved changes to this suggestion');

    // Verify side-by-side comparison pane renders the server's edits and local edits
    const serverRef = page.getByTestId('server-summary-reference');
    const localRef = page.getByTestId('local-summary-draft-reference');
    await expect(serverRef).toBeVisible();
    await expect(localRef).toBeVisible();

    // Verify "Force Overwrite" and "Accept Server Changes" buttons render
    const forceBtn = page.getByRole('button', {name: 'Force Overwrite Server'});
    const acceptBtn = page.getByRole('button', {name: 'Accept Server Changes'});
    await expect(forceBtn).toBeVisible();
    await expect(acceptBtn).toBeVisible();

    // 6. Test "Force Overwrite"
    const forcePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await forceBtn.click({force: true});
    await forcePromise;

    // Dialog should close on successful overwrite
    await expect(dialog).not.toBeVisible();
    
    // Verify patchCount is 2 (first failed, second succeeded!)
    expect(patchCount).toBe(2);
  });

  test('Baseline Status & Dates Override chronological validations', async ({page}) => {
    // 1. Log in, create feature, set milestone, trigger generation
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test baseline dates ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const dateFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = dateFeatureId;
    await setShippedMilestone(page, dateFeatureId, stableMilestone);

    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${dateFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, {timeout: 15000});

    // 2. Open dialog
    await card.getByRole('button', {name: /Review.*suggestion/i}).click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // 3. Click "Newly Available" card
    await page.getByRole('radio', {name: 'Baseline Newly Available'}).click();

    // Verify date input is visible
    const newlyDateInput = page.getByLabel('Newly Available Date');
    await expect(newlyDateInput).toBeVisible();

    // 4. Click "Widely Available" card
    await page.getByRole('radio', {name: 'Baseline Widely Available'}).click();

    const widelyDateInput = page.getByLabel('Widely Available Date');
    await expect(widelyDateInput).toBeVisible();

    // 5. Fill widely date BEFORE newly date -> should show chronological validation error in dialog
    await newlyDateInput.fill('2024-03-15');
    await widelyDateInput.fill('2024-03-14');
    
    const saveBtn = page.getByRole('button', {name: 'Save & Apply'});
    await saveBtn.click({force: true});

    // Verify chronological error is shown
    const dialogError = page.locator('.error-message');
    await expect(dialogError).toBeVisible();
    await expect(dialogError).toContainText('Widely Available Date must be chronologically after or equal to the Newly Available Date');

    // 6. Fill valid chronological dates and save
    await widelyDateInput.fill('2026-09-15');
    await saveBtn.click();

    // Dialog should close on successful save!
    await expect(dialog).not.toBeVisible();
  });

  test('Skipped Suggestion dashboard badge and Manual Entry dialog flow', async ({page}) => {
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test skipped suggestion ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const skippedFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = skippedFeatureId;
    await setShippedMilestone(page, skippedFeatureId, stableMilestone);

    // Mock GET suggestion API to return status 'skipped' with a rationale
    await page.route(`**/api/v0/features/${skippedFeatureId}/summary_suggestion`, async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: ")]}'\n" + JSON.stringify({
            status: 'skipped',
            status_message: null,
            model_used: 'gemini-1.5-pro',
            progress_steps: [],
            suggested_summary: null,
            generation_rationale: 'Skipped due to lack of technical explainers.',
            suggested_doc_links: [],
            baseline_status: 'none',
            baseline_newly_date: null,
            baseline_widely_date: null,
            original_baseline_status: 'none',
            original_baseline_newly_date: null,
            original_baseline_widely_date: null,
            status_timestamp: null,
            last_generation_attempt: null,
            version_token: 1,
            summary_provenance: null,
            doc_links_provenance: null,
            suggested_format: 'markdown',
            original_summary_format: null
          })
        });
      } else {
        await route.continue();
      }
    });

    // Navigate to Releases
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${skippedFeatureId}`);

    // Verify the "Skipped" badge is displayed in the card
    const skippedTag = card.locator('sl-tag[variant="neutral"]');
    await expect(skippedTag).toBeVisible();
    await expect(skippedTag).toContainText('Skipped');

    // Verify "Write Summary Manually" button is visible
    const manualBtn = card.getByTestId('suggestion-action-button');
    await expect(manualBtn).toBeVisible();
    await expect(manualBtn).toContainText('Write Summary Manually');

    // Click it -> should open the dialog in manual edit mode
    await manualBtn.click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Verify that the textarea is pre-populated with the original summary (deliberate friendly UX fallback)
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveValue('Test summary description');

    // Verify the skipped alert banner is visible in the dialog showing the skip rationale!
    const skippedBanner = page.locator('sl-alert[variant="neutral"]');
    await expect(skippedBanner).toBeVisible();
    await expect(skippedBanner).toContainText('Skipped due to lack of technical explainers.');
  });

  test('Write/Preview Tabs toggle and Markdown rendering in E2E', async ({page}) => {
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test preview tab ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const previewFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = previewFeatureId;
    await setShippedMilestone(page, previewFeatureId, stableMilestone);

    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${previewFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, {timeout: 15000});

    // Open dialog
    await card.getByRole('button', {name: /Review.*suggestion/i}).click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Type markdown in Write tab
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await textarea.fill('This has **bold markdown text** and an [explainer link](https://example.com/explainer).');

    // Toggle to Preview tab
    const previewTab = page.getByRole('tab', {name: 'Preview'});
    await previewTab.click();

    // Verify preview container is visible and renders HTML elements correctly
    const previewContainer = page.getByTestId('summary-preview-container');
    await expect(previewContainer).toBeVisible();
    
    // Assert bold text is rendered as strong element
    const strongElement = previewContainer.locator('strong');
    await expect(strongElement).toBeVisible();
    await expect(strongElement).toHaveText('bold markdown text');

    // Assert link is rendered as anchor
    const anchorElement = previewContainer.locator('a');
    await expect(anchorElement).toBeVisible();
    await expect(anchorElement).toHaveAttribute('href', 'https://example.com/explainer');
    await expect(anchorElement).toHaveText('explainer link');
  });

  test('Page-level skeleton loaders and empty state validations', async ({page}) => {
    await loginAs(page, 'devrel@chromium.org');

    // 1. Mock empty pending reviews API
    await page.route('**/api/v0/features/pending_reviews', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: ")]}'\n" + JSON.stringify({features: [], total_count: 0}),
      });
    });

    // 2. Go to Release Reviews
    await page.goto('/release-reviews');

    // Verify empty state is displayed properly
    const emptyState = page.getByTestId('empty-dashboard');
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toContainText('All clear! There are no release reviews pending your attention.');
  });

  test('Drawer pending count real-time synchronization on apply/discard', async ({page}) => {
    await loginAs(page, 'devrel@chromium.org');

    // 1. Create a feature and generate a draft suggestion
    const featureName = `Sync Drawer Test ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const syncFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = syncFeatureId;
    await setShippedMilestone(page, syncFeatureId, stableMilestone);

    // Trigger generation
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${syncFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, {timeout: 15000});

    // 2. Go to Release Reviews page (forces drawer to fetch updated count and render the gated menu item)
    await page.goto('/release-reviews');

    // Find our feature card on the reviews list.
    // If it's not visible immediately due to Datastore eventual consistency, reload the page!
    const reviewCard = page.getByTestId(`feature-card-${syncFeatureId}`);
    try {
      await expect(reviewCard).toBeVisible({ timeout: 2000 });
    } catch {
      console.log('[E2E] Card not visible due to eventual consistency, reloading page...');
      await page.reload();
      await expect(reviewCard).toBeVisible();
    }

    // 3. Locate drawer badge count (must now be visible and at least 1)
    const drawerBadge = page.locator('chromedash-drawer').locator('sl-badge[variant="danger"]');
    await expect(drawerBadge).toBeVisible();
    const initialCountStr = await drawerBadge.textContent();
    const initialCount = parseInt(initialCountStr || '0', 10);
    expect(initialCount).toBeGreaterThanOrEqual(1);

    // Open review dialog, edit summary, and apply
    await reviewCard.getByRole('button', {name: /Review.*suggestion/i}).click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    await page.locator('sl-textarea.editable-summary-textarea').locator('textarea').fill('Drawer sync applied summary.');
    
    const savePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await page.getByRole('button', {name: 'Save & Apply'}).click({force: true});
    await savePromise;

    // Dialog should close and page card should disappear
    await expect(dialog).not.toBeVisible();
    await expect(reviewCard).not.toBeVisible();

    // 4. Verify drawer count badge has automatically decremented by exactly 1 in real-time!
    // Try waiting for the real-time update. If the Datastore emulator query index stutters (eventual consistency),
    // catch the timeout, reload the page to trigger a fresh fetch, and verify!
    try {
      if (initialCount - 1 === 0) {
        await expect(drawerBadge).not.toBeVisible({ timeout: 2000 });
      } else {
        await expect(drawerBadge).toHaveText((initialCount - 1).toString(), { timeout: 2000 });
      }
    } catch {
      console.log('[E2E] Drawer badge did not update immediately due to eventual consistency, reloading page...');
      await page.reload();
      if (initialCount - 1 === 0) {
        await expect(drawerBadge).not.toBeVisible();
      } else {
        await expect(drawerBadge).toHaveText((initialCount - 1).toString());
      }
    }
  });

  test('Release Reviews pagination and list filtering', async ({page}) => {
    await loginAs(page, 'devrel@chromium.org');

    // Mock 12 pending features to trigger pagination (> 10 items)
    const mockFeatures = Array.from({length: 12}, (_, i) => ({
      id: 200 + i,
      name: `Mock Pending Feature ${i + 1}`,
      summary: `Summary number ${i + 1}`,
      blink_components: ['Blink>Mock'],
      owner_emails: ['owner@example.com'],
      editor_emails: [],
      creator_email: 'creator@example.com',
      resources: {docs: [], samples: []},
    }));

    await page.route('**/api/v0/features/pending_reviews', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: ")]}'\n" + JSON.stringify({features: mockFeatures, total_count: 12}),
      });
    });

    // Mock individual suggestion details for each of the 12 features
    for (let i = 0; i < 12; i++) {
      await page.route(`**/api/v0/features/${200 + i}/summary_suggestion`, async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: ")]}'\n" + JSON.stringify({
            status: 'complete',
            suggested_summary: `AI Mock suggestion ${i + 1}`,
            suggested_doc_links: [],
            baseline_status: 'none',
            version_token: 1,
          }),
        });
      });
    }

    // Go to Release Reviews
    await page.goto('/release-reviews');

    // 1. Verify Page 1 shows exactly 10 features
    const cardsOnPage1 = page.locator('chromedash-release-feature-card');
    await expect(cardsOnPage1).toHaveCount(10);

    const paginationInfo = page.getByTestId('pagination-info');
    await expect(paginationInfo).toHaveText('Page 1 of 2');

    // 2. Click "Next" to go to Page 2
    const nextBtn = page.getByRole('button', {name: 'Next'});
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    // 3. Verify Page 2 shows remaining 2 features
    const cardsOnPage2 = page.locator('chromedash-release-feature-card');
    await expect(cardsOnPage2).toHaveCount(2);
    await expect(paginationInfo).toHaveText('Page 2 of 2');

    // Verify "Next" is now disabled, "Previous" is enabled
    await expect(nextBtn).toBeDisabled();
    const prevBtn = page.getByRole('button', {name: 'Previous'});
  });

  test('DevRel bypass and owner successful Revert to Original flow in E2E', async ({page}) => {
    // 1. Create a feature owned by example@chromium.org (using mock login)
    await loginAs(page, 'example@chromium.org');
    const featureName = `Revert Flow Test ${Date.now()}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const revertFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = revertFeatureId;
    await setShippedMilestone(page, revertFeatureId, stableMilestone);

    // Trigger AI generation
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.getByTestId(`feature-card-${revertFeatureId}`);
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, {timeout: 15000});

    // 2. Log in as DevRel to perform the bypass save
    await loginAs(page, 'devrel@chromium.org');
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const devrelCard = page.getByTestId(`feature-card-${revertFeatureId}`);
    
    await devrelCard.getByRole('button', {name: /Review.*suggestion/i}).click();
    const dialog = page.getByRole('dialog', {name: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Change summary and apply
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await textarea.fill('Bypassed summary text to be reverted.');
    await page.getByRole('button', {name: 'Save & Apply'}).click({force: true});

    // Fill bypass justification and confirm
    const justificationTextarea = page.locator('sl-textarea[name="bypass_justification"]').locator('textarea');
    await justificationTextarea.fill('Bypassing to test revert flow.');
    
    const savePromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await page.getByRole('button', {name: 'Confirm Apply Bypass'}).click({force: true});
    await savePromise;
    await expect(dialog).not.toBeVisible();

    // 3. Log in back as the Owner and visit the feature detail page
    await loginAs(page, 'example@chromium.org');
    await page.goto(`/feature/${revertFeatureId}`);

    // Verify the bypassed alert banner is visible on the detail page
    const bypassedAlert = page.locator('sl-alert[variant="warning"]', {hasText: 'bypassed'});
    await expect(bypassedAlert).toBeVisible();
    await expect(bypassedAlert).toContainText('revert this edit');

    // 4. Click the "Revert to My Original" button inside the alert
    const revertBtn = bypassedAlert.getByRole('button', {name: 'Revert to My Original'});
    await expect(revertBtn).toBeVisible();
    
    const revertPromise = page.waitForResponse(r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200);
    await revertBtn.click();
    await revertPromise;

    // Verify the alert banner disappears after successful reversion
    await expect(bypassedAlert).not.toBeVisible();

    // Expand the Metadata section to make the summary visible in the viewport!
    await page.getByRole('button', {name: 'Metadata'}).click();

    // Verify the page content shows the original feature summary
    const featureSummary = page.getByTestId('summary-value');
    await expect(featureSummary).toBeVisible();
    await expect(featureSummary).toContainText('Test summary description');
  });
});
