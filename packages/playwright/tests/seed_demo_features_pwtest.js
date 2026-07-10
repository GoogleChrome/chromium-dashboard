import { test, expect } from '@playwright/test';
import {
  createNewFeature,
  loginAs,
} from './test_utils';

const API_PREFIX = ")]}'\n";

async function setFeatureCurationDetails(page, featureId, milestone, explainer, spec) {
  console.log(`[Seeder] Setting curation details for feature ${featureId} (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1000);

  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());

  const explainerInput = page.locator('textarea[name="explainer_links"]');
  await explainerInput.scrollIntoViewIfNeeded();
  await expect(explainerInput).toBeVisible();
  await explainerInput.fill(explainer);

  const specInput = page.locator('input[name="spec_link"]');
  await specInput.scrollIntoViewIfNeeded();
  await expect(specInput).toBeVisible();
  await specInput.fill(spec);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(1500);
}

test('Seed Rachel Andrew Demo Features', async ({ page, request }) => {
  test.setTimeout(120000); // 2 minutes

  await page.route('https://accounts.google.com/**', route => route.abort());

  // Fetch stable milestone dynamically
  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;
  console.log(`[Seeder] Detected stable milestone: ${stableMilestone}`);

  console.log('[Seeder] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(1500);

  // 1. Create Feature A: Prompt API
  console.log('[Seeder] Step 2: Creating Prompt API feature');
  const promptSummary = "Prompt API gives web developers direct access to a browser-provided on-device AI language model. This API has been shipped in Chrome Extensions. An enterprise policy GenAILocalFoundationalModelSettings is available to disable the underlying model downloading, which would render this API unavailable. Enterprise admins can also set the BuiltInAIAPIsEnabled policy to block Built-In AI API usage, while still permitting other on-device GenAI features. Language support log: Chrome M139 and earlier only supported English, M140 added support for Spanish and Japanese. The initial implementation supports text, image, and audio inputs. In addition, response constraints ensure that generated text conforms with predefined regex and JSON schema formats.";
  await createNewFeature(page, "Prompt API", promptSummary);
  
  let parts = page.url().split('/');
  let promptId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(1000);

  console.log('[Seeder] Step 3: Setting Curation Details for Prompt API');
  await setFeatureCurationDetails(
    page,
    promptId,
    stableMilestone,
    "https://github.com/webmachinelearning/prompt-api/blob/main/README.md",
    "http://webmachinelearning.github.io/prompt-api"
  );

  // 2. Create Feature B: CSS Gap Decorations
  console.log('[Seeder] Step 4: Creating CSS Gap Decorations feature');
  const cssSummary = "CSS Gap Decorations enables styling of gaps in container layouts like Grid and Flexbox, similar to 'column-rule' in multicol layout. This feature is highly requested by web authors who must use hacks to style the gaps in Grid and Flexbox layouts today.";
  await createNewFeature(page, "CSS Gap Decorations", cssSummary);
  
  parts = page.url().split('/');
  let cssId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(1000);

  console.log('[Seeder] Step 5: Setting Curation Details for CSS Gap Decorations');
  await setFeatureCurationDetails(
    page,
    cssId,
    stableMilestone,
    "https://github.com/MicrosoftEdge/MSEdgeExplainers/blob/main/CSSGapDecorations/explainer.md",
    "https://drafts.css-gaps-1"
  );

  console.log('[Seeder] All demo features successfully created and configured! 🎉');
  console.log(`[Seeder] Prompt API ID: ${promptId}`);
  console.log(`[Seeder] CSS Gap Decorations ID: ${cssId}`);
});
