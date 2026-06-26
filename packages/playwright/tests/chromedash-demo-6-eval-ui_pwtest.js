// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
} from './test_utils';
import { demoFeatures } from './demo_features';

async function setFeatureWptDetails(page, featureId, spec, wptDescr, explainer) {
  console.log(`[Demo 6] Setting WPT evaluation prerequisites (Spec: ${spec})...`);
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1500); // Visual pause

  const specInput = page.locator('input[name="spec_link"]');
  await specInput.scrollIntoViewIfNeeded();
  await specInput.fill(spec);
  await page.waitForTimeout(500);

  const wptDescrInput = page.locator('textarea[name="wpt_descr"]');
  await wptDescrInput.scrollIntoViewIfNeeded();
  await wptDescrInput.fill(wptDescr);
  await page.waitForTimeout(500);

  const explainerInput = page.locator('textarea[name="explainer_links"]');
  await explainerInput.scrollIntoViewIfNeeded();
  await explainerInput.fill(explainer);
  await page.waitForTimeout(800);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(2000); // Pause
}

test('Demo 6: AI-Powered WPT Coverage Evaluation Dashboard', async ({ page }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(120000); // 2-minute runway for live Gemini WPT analysis

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  console.log('[Demo 6] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  console.log('[Demo 6] Step 2: Creating a new Popover API feature');
  const targetFeature = demoFeatures.popover;
  const uniqueFeatureName = `${targetFeature.name} (WPT Analysis) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 6] Step 3: Setting Spec URL and WPT fyi Results links');
  const wptDescrText = `Here are the official Web Platform Test results for the Popover API:
  https://wpt.fyi/results/html/semantics/popovers`;
  await setFeatureWptDetails(page, featureId, targetFeature.spec, wptDescrText, targetFeature.explainer);

  console.log('[Demo 6] Step 4: Navigating to WPT Coverage Evaluation Dashboard');
  await page.goto(`/feature/${featureId}/ai-coverage-analysis`);
  await page.waitForTimeout(3000); // Pause to let the prerequisites checklist render beautifully

  // Verify the checklist shows all green checkmarks!
  const checklist = page.locator('section.card').first();
  await expect(checklist).toContainText('provided');
  await page.waitForTimeout(1000);

  console.log('[Demo 6] Step 5: Clicking "Generate Report"');
  const generateBtn = page.getByRole('button', { name: 'Generate WPT Coverage' });
  await generateBtn.hover();
  await page.waitForTimeout(800);
  await generateBtn.click();

  console.log('[Demo 6] Step 6: Waiting for the AI-Powered WPT analysis to complete');
  // Wait for the report card to render (takes ~15-20 seconds for the live Gemini WPT evaluator)
  const reportCard = page.locator('.report-content');
  await expect(reportCard).toBeVisible({ timeout: 45000 });
  await page.waitForTimeout(2000);

  console.log('[Demo 6] Step 7: Showcasing the generated WPT Coverage Report!');
  // Scroll slowly through the report to show off the visual layout and key coverage insights
  await reportCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(3000); // Let viewer read the top sections

  // Scroll down to the test gaps breakdown
  const scrollHeight = await reportCard.evaluate(node => node.scrollHeight);
  await reportCard.evaluate((node, height) => {
    node.scrollTo({ top: height / 2, behavior: 'smooth' });
  }, scrollHeight);
  await page.waitForTimeout(3000);

  // Scroll to the bottom
  await reportCard.evaluate((node, height) => {
    node.scrollTo({ top: height, behavior: 'smooth' });
  }, scrollHeight);
  await page.waitForTimeout(4000); // Final pause on the completed evaluation
});
