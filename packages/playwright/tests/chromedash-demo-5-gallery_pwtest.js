// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
} from './test_utils';
import { demoFeatures } from './demo_features';

const API_PREFIX = ")]}'\n";

async function seedFeatureForGallery(page, featureData, milestone) {
  console.log(`[Demo 5] Seeding feature: ${featureData.name}...`);
  
  // Step 1: Create basic feature
  const uniqueName = `${featureData.name} - ${Date.now()}`;
  await createNewFeature(page, uniqueName, featureData.summary);
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(1000);

  // Step 2: Set curation details on editall page
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1000);

  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await milestoneInput.fill(milestone.toString());

  const explainerInput = page.locator('textarea[name="explainer_links"]');
  await explainerInput.scrollIntoViewIfNeeded();
  await explainerInput.fill(featureData.explainer);

  const specInput = page.locator('input[name="spec_link"]');
  await specInput.scrollIntoViewIfNeeded();
  await specInput.fill(featureData.spec);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(1500);

  // Step 3: Go to Releases page, trigger generation (mock is fine since we override it)
  await page.goto(`/releases?milestone=${milestone}`);
  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible({ timeout: 20000 });
  
  const generateBtn = card.getByRole('button', { name: 'Generate Summary' });
  await generateBtn.click();
  
  // Wait for draft badge (give live Gemini Agent ample time to search MDN and verify links)
  const suggestionBadge = card.locator('sl-tag[variant="success"]');
  await expect(suggestionBadge).toHaveText(/Draft Available/, { timeout: 75000 });
  await page.waitForTimeout(1000);

  // Step 4: Open review dialog, paste real technical summary, and apply
  const reviewBtn = card.getByRole('button', { name: /Review.*suggestion/i });
  await reviewBtn.click();
  
  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(1000);

  const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
  await textarea.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(300);
  // Instantly fill the real, beautiful technical summary!
  await textarea.fill(featureData.summary);
  await page.waitForTimeout(500);

  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.click({ force: true });
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(1500);
  
  console.log(`[Demo 5] Feature ${featureData.name} successfully curated!`);
}

test('Demo 5: Curated Milestone Releases Gallery Showcase', async ({ page, request }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(300000); // 5-minute runway to seed 3 features and record the gallery walk-through with live Gemini runs!

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  console.log('[Demo 5] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  // Seed the three real-world features into the stable milestone
  console.log('[Demo 5] Step 2: Seeding Popover API');
  await seedFeatureForGallery(page, demoFeatures.popover, stableMilestone);

  console.log('[Demo 5] Step 3: Seeding CSS Painting API');
  await seedFeatureForGallery(page, demoFeatures.cssPaint, stableMilestone);

  console.log('[Demo 5] Step 4: Seeding CSS Anchor Positioning');
  await seedFeatureForGallery(page, demoFeatures.anchorPositioning, stableMilestone);

  // Step 5: Navigate to Releases page and showcase the gallery!
  console.log('[Demo 5] Step 5: Showcasing the fully-populated Curated Releases Page!');
  await page.goto(`/releases?milestone=${stableMilestone}`);
  await page.waitForTimeout(3000); // Hold starting screen

  // Slowly scroll the page down to show all curated cards beautifully
  const mainContent = page.locator('main');
  
  console.log('[Demo 5] Scrolling to first card...');
  const card1 = page.locator('chromedash-release-feature-card').nth(0);
  await card1.scrollIntoViewIfNeeded();
  await page.waitForTimeout(2500); // Pause to let viewer read

  console.log('[Demo 5] Scrolling to second card...');
  const card2 = page.locator('chromedash-release-feature-card').nth(1);
  await card2.scrollIntoViewIfNeeded();
  await page.waitForTimeout(2500);

  console.log('[Demo 5] Scrolling to third card...');
  const card3 = page.locator('chromedash-release-feature-card').nth(2);
  await card3.scrollIntoViewIfNeeded();
  await page.waitForTimeout(4000); // Final pause on the gorgeous curated dashboard
});
