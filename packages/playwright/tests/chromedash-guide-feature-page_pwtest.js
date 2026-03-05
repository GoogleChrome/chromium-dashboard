// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
} from './test_utils';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(90000);

  // Login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  // Logout after running each test.
  await logout(page);
});

test('add an origin trial stage', async ({page}) => {
  // Safest way to work with a unique feature is to create it.
  await createNewFeature(page);

  // Add an origin trial stage.
  const addStageButton = page.getByText('Add stage');
  await addStageButton.click();

  // Select stage to create.
  const stageSelect = page.locator('sl-select#stage_create_select');

  // Set up a promise to wait for the dropdown to completely finish opening and positioning.
  const selectOpenedPromise = stageSelect.evaluate(
    node =>
      new Promise(resolve =>
        node.addEventListener('sl-after-show', resolve, {once: true})
      )
  );

  await stageSelect.click();

  // Wait for the event to fire before proceeding.
  await selectOpenedPromise;

  // Wait for the option to appear in the dropdown.
  const originTrialStageOption = page.locator(
    'sl-select sl-option[value="150"]'
  );
  await expect(originTrialStageOption).toBeVisible();

  // Hover Origin trial stage option.
  await originTrialStageOption.hover();

  // Click the origin trial stage option to prepare to create stage.
  await originTrialStageOption.click();

  // Click the Create stage button to finally create the stage.
  const createStageButton = page.getByText('Create stage');
  await createStageButton.click();

  // Check we are still on the feature page (waits for navigation/URL update).
  await page.waitForURL('**/feature/*', {timeout: 5000});

  // Expand the "Origin Trial" and "Origin Trial 2" panels
  const originTrialPanel = page.locator('sl-details[summary="Origin Trial"]');
  const originTrial2Panel = page.locator(
    'sl-details[summary="Origin Trial 2"]'
  );

  await originTrialPanel.click();
  await originTrial2Panel.click();

  // Wait for the expansion to finish.
  // We do this by checking if the "Edit" button inside the panel is visible.
  const editButton1 = originTrialPanel.locator(
    'sl-button[href^="/guide/stage"]'
  );
  const editButton2 = originTrial2Panel.locator(
    'sl-button[href^="/guide/stage"]'
  );
  await expect(editButton1).toBeVisible();
  await expect(editButton2).toBeVisible();

  // Take a screenshot of the content area.
  // First scroll to "Prepare to ship" panel to frame the shot.
  const prepareToShipPanel = page.getByText('Prepare to ship');
  await prepareToShipPanel.scrollIntoViewIfNeeded();

  // Move the mouse out of the way to prevent accidental hover states.
  await page.mouse.move(0, 0);

  await expect(page).toHaveScreenshot('origin-trial-panels.png', {
    mask: [page.locator('section[id="history"]')],
  });
});
