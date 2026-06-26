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
  console.log(`[Demo 1] Setting curation details (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
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

test('Demo 1: AI Summary Generation & Draft Status Badge', async ({ page, request }) => {
  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  // Fetch stable milestone dynamically
  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  console.log('[Demo 1] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  console.log('[Demo 1] Step 2: Creating a new real-world feature');
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 1] Step 3: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  console.log('[Demo 1] Step 4: Navigating to Releases Page');
  await page.goto(`/releases?milestone=${stableMilestone}`);
  await page.waitForTimeout(2500); // Allow dashboard to load beautifully

  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible();
  await card.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  console.log('[Demo 1] Step 5: Triggering AI Summary Generation');
  const generateBtn = card.getByRole('button', { name: 'Generate Summary' });
  await expect(generateBtn).toBeVisible();
  await page.waitForTimeout(1000);
  
  await generateBtn.hover();
  await page.waitForTimeout(800);
  await generateBtn.click();

  console.log('[Demo 1] Step 6: Waiting for the Draft Available badge');
  const suggestionBadge = card.locator('sl-tag[variant="success"]');
  // Dynamic timeout up to 25 seconds for real live Gemini generation with tool lookups
  await expect(suggestionBadge).toHaveText(/Draft Available/, { timeout: 25000 });
  await page.waitForTimeout(3000); // Hold final screen
});
