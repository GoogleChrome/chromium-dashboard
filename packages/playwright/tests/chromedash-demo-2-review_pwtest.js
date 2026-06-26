// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
} from './test_utils';
import { demoFeatures } from './demo_features';

const API_PREFIX = ")]}'\n";

async function setFeatureCurationDetails(page, featureId, milestone, explainer, spec) {
  console.log(`[Demo 2] Setting curation details (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1500); // Visual pause for pacing

  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());
  await page.waitForTimeout(500);

  const explainerInput = page.locator('textarea[name="explainer_links"]');
  await explainerInput.scrollIntoViewIfNeeded();
  await expect(explainerInput).toBeVisible();
  await explainerInput.fill(explainer);
  await page.waitForTimeout(500);

  const specInput = page.locator('input[name="spec_link"]');
  await specInput.scrollIntoViewIfNeeded();
  await expect(specInput).toBeVisible();
  await specInput.fill(spec);
  await page.waitForTimeout(800);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(2000); // Visual pause after save
}

async function typeSlowly(page, locator, text) {
  console.log(`[Demo 2] Typing slowly: "${text}"`);
  await locator.focus();
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(45); // 45ms per char for natural visual typing pacing
  }
  await page.waitForTimeout(500);
}

test('Demo 2: Symmetrical Review Dialog Workspace & Markdown Editing', async ({ page, request }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(120000); // Give a generous 120s runway for live LLM generation and extensive slow-mo UI editing!

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  console.log('[Demo 2] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 2: Creating a new real-world feature');
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} (Review) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 3: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  console.log('[Demo 2] Step 4: Navigating to Releases Page & Triggering AI Generation');
  await page.goto(`/releases?milestone=${stableMilestone}`);
  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible();
  await card.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  const generateBtn = card.getByRole('button', { name: 'Generate Summary' });
  await generateBtn.click();

  // Wait for the status badge to change to "Draft Available"
  const suggestionBadge = card.locator('sl-tag[variant="success"]');
  await expect(suggestionBadge).toHaveText(/Draft Available/, { timeout: 75000 });
  await page.waitForTimeout(2000); // Visual pause

  console.log('[Demo 2] Step 5: Clicking "Review Suggestion"');
  const reviewBtn = card.getByRole('button', { name: /Review.*suggestion/i });
  await reviewBtn.hover();
  await page.waitForTimeout(800);
  await reviewBtn.click();

  console.log('[Demo 2] Step 6: Symmetrical dialog opened');
  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2500); // Pause to let the viewer see the symmetrical layout

  console.log('[Demo 2] Step 7: Demonstrating Write/Preview Tabs');
  const previewTab = page.getByRole('tab', { name: 'Preview' });
  const writeTab = page.getByRole('tab', { name: 'Write' });
  
  await previewTab.hover();
  await page.waitForTimeout(500);
  await previewTab.click();
  await page.waitForTimeout(1500); // Look at live preview of generated text

  await writeTab.hover();
  await page.waitForTimeout(500);
  await writeTab.click();
  await page.waitForTimeout(1000);

  console.log('[Demo 2] Step 8: Editing the summary with Markdown in slow-mo');
  const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
  await textarea.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(800);

  // Type a polished summary that relates directly to the real feature!
  const polishedSummary = `This feature **simplifies tooltip and popup positioning** by introducing a native browser-supported anchoring workflow. It tether-positions elements relative to one or more anchor elements, eliminating the need for complex JavaScript calculations like Popper.js!`;
  await typeSlowly(page, textarea, polishedSummary);
  await page.waitForTimeout(1500);

  console.log('[Demo 2] Step 9: Toggling to Preview tab to show live Markdown rendering');
  await previewTab.click();
  await page.waitForTimeout(2500); // Let viewer inspect bold text, punctuation, and links

  console.log('[Demo 2] Step 10: Approving / Pruning documentation links');
  await writeTab.click();
  await page.waitForTimeout(1000);

  // Locate the checkbox items (which were populated by the real Gemini call!)
  const firstCheckbox = page.locator('sl-checkbox.link-checkbox').first();
  if (await firstCheckbox.isVisible()) {
    await firstCheckbox.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await firstCheckbox.hover();
    await page.waitForTimeout(500);
    await firstCheckbox.click(); // Toggle approval state
    await page.waitForTimeout(1200);
  }

  console.log('[Demo 2] Step 11: Overriding WebDX Baseline status cards');
  const baselineNewlyRadio = page.getByRole('radio', { name: 'Baseline Newly Available' });
  await baselineNewlyRadio.scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await baselineNewlyRadio.hover();
  await page.waitForTimeout(500);
  await baselineNewlyRadio.click();
  await page.waitForTimeout(1500); // Observe Newly Available date field expanding

  // Fill in Newly Available Date
  const newlyDateInput = page.getByLabel('Newly Available Date');
  await newlyDateInput.focus();
  await page.waitForTimeout(500);
  await newlyDateInput.fill('2026-06-25');
  await page.waitForTimeout(1500);

  console.log('[Demo 2] Step 12: Saving & Applying edits');
  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.hover();
  await page.waitForTimeout(800);
  await saveBtn.click({ force: true });

  // Dialog closes, back to dashboard
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(3000); // Hold final screen showing updated badge
});
