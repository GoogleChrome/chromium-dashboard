// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
  expectScreenshot,
} from './test_utils';

test.describe('Release Notes SSR Page', () => {
  test.beforeEach(async ({page}, testInfo) => {
    captureConsoleMessages(page);
    testInfo.setTimeout(60000);
    await login(page);
  });

  test.afterEach(async ({page}) => {
    await logout(page);
  });

  test('should render symmetrical navigation strip with channel quick-jumps and active pills', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const pageHeading = page.getByRole('heading', {
      name: 'Chrome 151 Release Notes',
    });
    await expect(pageHeading).toBeVisible();

    const navStrip = page.locator('.nav-strip');
    await expect(navStrip).toBeVisible();

    const stableLink = navStrip.getByRole('link', {name: /^Stable/i});
    const betaLink = navStrip.getByRole('link', {name: /^Beta/i});
    const devLink = navStrip.getByRole('link', {name: /^Dev/i});

    await expect(stableLink).toBeVisible();
    await expect(betaLink).toBeVisible();
    await expect(devLink).toBeVisible();

    await expect(stableLink).toHaveAttribute('href', /\/release-notes\/\d+/);
    await expect(betaLink).toHaveAttribute('href', /\/release-notes\/\d+/);
    await expect(devLink).toHaveAttribute('href', /\/release-notes\/\d+/);

    const activePill = page.locator('.channel-pill.active');
    await expect(activePill).toBeVisible();
  });

  test('should navigate to selected milestone via milestone combobox selector dropdown', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const milestoneSelect = page.getByLabel('Milestone:');
    await expect(milestoneSelect).toBeVisible();
    await expect(milestoneSelect).toHaveValue('151');

    await milestoneSelect.selectOption('152');
    await page.waitForURL(/\/release-notes\/152/, {timeout: 10000});

    const newHeading = page.getByRole('heading', {
      name: 'Chrome 152 Release Notes',
    });
    await expect(newHeading).toBeVisible();
    await expect(milestoneSelect).toHaveValue('152');
  });

  test('should render populated release notes page with features and take visual snapshot', async ({
    page,
  }) => {
    // 1. Create a feature in the Datastore emulator.
    await createNewFeature(page);

    // 2. Extract feature ID and update its shipped milestone to 151 via editall form.
    const url = page.url();
    const match = url.match(/\/feature\/(\d+)/);
    expect(match).not.toBeNull();
    const featureId = match[1];

    await page.goto(`/guide/editall/${featureId}`, {timeout: 30000});
    await expect(page.locator('chromedash-form-table')).toBeVisible({
      timeout: 30000,
    });

    const shippedInput = page.locator('input[name="shipped_milestone"]');
    await shippedInput.fill('151');

    const submitButton = page.locator('input[type="submit"]');
    await submitButton.click();
    await page.waitForURL(`**/feature/${featureId}*`, {timeout: 30000});

    // 3. Navigate to SSR Release Notes for milestone 151.
    await page.goto('/release-notes/151', {timeout: 30000});

    const pageHeading = page.getByRole('heading', {
      name: 'Chrome 151 Release Notes',
    });
    await expect(pageHeading).toBeVisible();

    const featureCards = page.locator('.feature-card');
    await expect(featureCards.first()).toBeVisible({timeout: 20000});

    // 4. Sanitize dynamic feature IDs and links to ensure stable visual baselines across test runs.
    await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.feature-card'));
      cards.forEach((card, idx) => {
        card.id = `feature-static-${idx + 1}`;
        const link = card.querySelector('.feature-name');
        if (link && link instanceof HTMLAnchorElement) {
          link.href = '/feature/123456';
        }
      });
    });

    // 5. Capture visual snapshot of populated M151 page.
    await expectScreenshot(page, 'release-notes-ssr-m151-populated');
  });

  test('should render documentation and spec links with target=_blank and rel=noopener', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const docLinks = page.locator('.feature-doc-links a');
    const docLinksCount = await docLinks.count();

    if (docLinksCount > 0) {
      for (let i = 0; i < docLinksCount; i++) {
        const link = docLinks.nth(i);
        await expect(link).toHaveAttribute('target', '_blank');
        await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      }
    }
  });

  test('should perform HTTP 302 redirect for historical milestones prior to M151 cutoff', async ({
    page,
  }) => {
    await page.goto('/release-notes/150', {timeout: 30000});
    await expect(page).toHaveURL(/developer\.chrome\.com\/release-notes\/150/);
  });

  test('should render category section anchors and feature card ID anchors', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const categorySections = page.locator('.category-section');
    const categoryCount = await categorySections.count();

    if (categoryCount > 0) {
      const firstCategory = categorySections.first();
      await expect(firstCategory).toHaveAttribute('id', /^[a-z0-9-]+$/);

      const categoryTitle = firstCategory.locator('.category-title');
      await expect(categoryTitle).toBeVisible();
      await expect(categoryTitle).toHaveAttribute(
        'id',
        /^category-[a-z0-9-]+$/
      );

      const featureCards = firstCategory.locator('.feature-card');
      const cardCount = await featureCards.count();
      if (cardCount > 0) {
        await expect(featureCards.first()).toHaveAttribute(
          'id',
          /^feature-\d+$/
        );
      }
    }
  });

  test('should render empty state for milestone 152 and take visual snapshot', async ({
    page,
  }) => {
    await page.goto('/release-notes/152', {timeout: 30000});

    const emptyState = page.locator('.empty-state');
    await expect(emptyState).toBeVisible({timeout: 20000});
    await expect(emptyState.getByRole('heading')).toHaveText(
      'No release notes features available for Chrome 152.'
    );

    // Capture visual snapshot of empty state M152 page.
    await expectScreenshot(page, 'release-notes-ssr-m152-empty');
  });
});
