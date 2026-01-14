// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, login, logout,
  createNewFeature
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
  // Ensure it is open before proceeding (using the open attribute of sl-details)
  await expect(incubatingPanel).toHaveAttribute('open', '');

  // Add an origin trial stage.
  const addStageButton = page.getByText('Add stage');
  await addStageButton.click();

  // Select stage to create.
  const stageSelect = page.locator('sl-select#stage_create_select');
  await stageSelect.click();

  // Wait for the option to appear in the dropdown.
  const originTrialStageOption = page.locator('sl-select sl-option[value="150"]');
  await expect(originTrialStageOption).toBeVisible();

  // Hover Origin trial stage option.
  await originTrialStageOption.hover();

  // Screenshot of this dialog.
  await expect(page).toHaveScreenshot('create-origin-trial-stage-dialog.png', {
    mask: [page.locator('section[id="history"]')]
  });

  // Click the origin trial stage option to prepare to create stage.
  await originTrialStageOption.click();

  // Click the Create stage button to finally create the stage.
  const createStageButton = page.getByText('Create stage');
  await createStageButton.click();

  // Check we are still on the feature page (waits for navigation/URL update).
  await page.waitForURL('**/feature/*', { timeout: 5000 });

  // Expand the "Origin Trial" and "Origin Trial 2" panels
  const originTrialPanel = page.locator('sl-details[summary="Origin Trial"]');
  const originTrial2Panel = page.locator('sl-details[summary="Origin Trial 2"]');

  await originTrialPanel.click();
  await originTrial2Panel.click();

  // Wait for the expansion to finish.
  // We do this by checking if the "Edit" button inside the panel is visible.
  const editButton1 = originTrialPanel.locator('sl-button[href^="/guide/stage"]');
  const editButton2 = originTrial2Panel.locator('sl-button[href^="/guide/stage"]');
  await expect(editButton1).toBeVisible();
  await expect(editButton2).toBeVisible();

  // Take a screenshot of the content area.
  // First scroll to "Prepare to ship" panel to frame the shot.
  const prepareToShipPanel = page.getByText('Prepare to ship');
  await prepareToShipPanel.scrollIntoViewIfNeeded();

  await expect(page).toHaveScreenshot('origin-trial-panels.png', {
    mask: [page.locator('section[id="history"]')]
  });
});
