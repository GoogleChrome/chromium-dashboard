// @ts-check
import { test, expect } from '@playwright/test';
import {
    captureConsoleMessages, delay, login, logout,
    gotoNewFeaturePage, enterBlinkComponent, createNewFeature
} from './test_utils';


test.beforeEach(async ({ page }, testInfo) => {
    captureConsoleMessages(page);
    testInfo.setTimeout(90000);

    // Login before running each test.
    await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});


test('add an origin trial stage', async ({ page }) => {
    // Safest way to work with a unique feature is to create it.
    await createNewFeature(page);

    // Expand the "Start incubating" panel to scroll the history section away from the dialog we're testing.
    const incubatingPanel = page.locator('sl-details[summary="Start incubating"]');
    await incubatingPanel.click();

    // Add an origin trial stage.
    const addStageButton = page.getByText('Add stage');
    await addStageButton.click();
    await delay(500);

    // Select stage to create
    const stageSelect = page.locator('sl-select#stage_create_select');
    await stageSelect.click();
    await delay(500);

    // Hover Origin trial stage option.
    const originTrialStageOption = page.locator('sl-select sl-option[value="150"]');
    await originTrialStageOption.hover();
    await delay(500);

    // Screenshot of this dialog.
    await expect(page).toHaveScreenshot('create-origin-trial-stage-dialog.png', {
        mask: [page.locator('section[id="history"]')]
    });

    // Click the origin trial stage option to prepare to create stage.
    originTrialStageOption.click();
    await delay(500);

    // Click the Create stage button to finally create the stage.
    const createStageButton = page.getByText('Create stage');
    await createStageButton.click();
    await delay(500);

    // Check we are still on the feature page.
    await page.waitForURL('**/feature/*', { timeout: 5000 });
    await delay(500);

    // Expand the "Origin Trial" and "Origin Trial 2" panels
    const originTrialPanel = page.locator('sl-details[summary="Origin Trial"]');
    const originTrial2Panel = page.locator('sl-details[summary="Origin Trial 2"]');
    await originTrialPanel.click();
    await originTrial2Panel.click();
    await delay(500);

    // Take a screenshot of the content area.
    // First scroll to "Prepare to ship" panel
    const prepareToShipPanel = page.getByText('Prepare to ship');
    await prepareToShipPanel.scrollIntoViewIfNeeded();
    await delay(500);
    await expect(page).toHaveScreenshot('origin-trial-panels.png', {
        mask: [page.locator('section[id="history"]')]
    });
});

test('set the active stage', async ({page}) => {
  await createNewFeature(page);

  // Edit the metadata.
  const metadataSection = page.locator('sl-details[summary="Metadata"]');
  await metadataSection.click();

  await metadataSection.getByRole('link', {name: 'Edit fields'}).click();

  // Select the origin trial stage.
  const activeStageSelect = page.locator('sl-select[name="active_stage_id"]');
  await activeStageSelect.click();
  await activeStageSelect
    .locator('sl-option', {hasText: 'Origin Trial'})
    .click();
  // Save.
  await page.getByRole('button', {name: 'Submit'}).click();

  // Check the origin trial is active.
  await expect(
    page
      .locator('sl-details')
      .getByRole('button', {name: 'Origin Trial - Active', expanded: true})
  ).toBeVisible();
});
