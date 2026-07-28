// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
} from './test_utils';

test.describe('Release Notes SSR Page', () => {
  let sharedFeatureName = '';

  test.beforeAll(async ({browser}) => {
    const page = await browser.newPage();
    captureConsoleMessages(page);
    await login(page);

    sharedFeatureName = `Release Notes Test Feature M151 ${Date.now()}`;
    await createNewFeature(page, {
      name: sharedFeatureName,
      summary: 'Test summary description for milestone 151 release notes.',
      milestone: 151,
    });

    await logout(page);
    await page.close();
  });

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

    const stableLink = page.getByRole('link', {name: /Stable/i});
    const betaLink = page.getByRole('link', {name: /Beta/i});
    const devLink = page.getByRole('link', {name: /Dev/i});

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

  test('should render created feature card and navigate to feature detail page', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const featureLink = page.getByRole('link', {name: sharedFeatureName});
    await expect(featureLink).toBeVisible({timeout: 20000});
    await expect(featureLink).toHaveClass(/feature-name/);

    await featureLink.click();
    await page.waitForURL(/\/feature\/\d+/, {timeout: 10000});

    const featureDetail = page.locator('chromedash-feature-detail');
    await expect(featureDetail).toBeVisible();
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

  test('should render empty state banner when milestone has no release notes features', async ({
    page,
  }) => {
    await page.goto('/release-notes/999', {timeout: 30000});

    const emptyState = page.locator('.empty-state');
    await expect(emptyState).toBeVisible();
    await expect(emptyState.getByRole('heading')).toHaveText(
      'No release notes features available for Chrome 999.'
    );
  });
});
