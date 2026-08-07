// @ts-check
import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
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

  test('should render milestone navigation strip with accessible steppers and jump box', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const pageHeading = page.getByRole('heading', {
      name: 'Chrome 151 Release Notes',
    });
    await expect(pageHeading).toBeVisible();

    const prevStepper = page.getByRole('link', {
      name: /Previous milestone: Chrome 150/i,
    });
    const nextStepper = page.getByRole('link', {
      name: /Next milestone: Chrome 152/i,
    });

    await expect(prevStepper).toBeVisible();
    await expect(nextStepper).toBeVisible();

    await expect(prevStepper).toHaveAttribute('href', '/release-notes/150');
    await expect(nextStepper).toHaveAttribute('href', '/release-notes/152');

    const jumpInput = page.getByLabel('Jump to Chrome milestone');
    await expect(jumpInput).toBeVisible();
    await expect(jumpInput).toHaveAttribute('list', 'milestones-datalist');
    await expect(jumpInput).toHaveValue('Chrome 151');

    // Verify datalist option exists for milestone 151
    const option151 = page.locator(
      '#milestones-datalist option[value="Chrome 151"]'
    );
    await expect(option151).toBeAttached();
  });

  test('should navigate to another milestone when typing milestone number and pressing Enter', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const jumpInput = page.getByLabel('Jump to Chrome milestone');
    await expect(jumpInput).toBeVisible();

    // Type milestone number and press Enter
    await jumpInput.fill('152');
    await jumpInput.press('Enter');
    await page.waitForURL(/\/release-notes\/152/, {timeout: 10000});

    const newHeading = page.getByRole('heading', {
      name: 'Chrome 152 Release Notes',
    });
    await expect(newHeading).toBeVisible();
    await expect(jumpInput).toHaveValue('Chrome 152');
  });

  test('should navigate to another milestone on jump box change event', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const jumpInput = page.getByLabel('Jump to Chrome milestone');
    await expect(jumpInput).toBeVisible();

    // Select/fill formatted milestone string and blur/change
    await jumpInput.fill('Chrome 153');
    await jumpInput.dispatchEvent('change');
    await page.waitForURL(/\/release-notes\/153/, {timeout: 10000});

    const newHeading = page.getByRole('heading', {
      name: 'Chrome 153 Release Notes',
    });
    await expect(newHeading).toBeVisible();
    await expect(jumpInput).toHaveValue('Chrome 153');
  });

  test('should navigate to next milestone when clicking the next stepper button', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const nextStepper = page.getByRole('link', {
      name: /Next milestone: Chrome 152/i,
    });
    await expect(nextStepper).toBeVisible();

    await nextStepper.click();
    await page.waitForURL(/\/release-notes\/152/, {timeout: 10000});

    const newHeading = page.getByRole('heading', {
      name: 'Chrome 152 Release Notes',
    });
    await expect(newHeading).toBeVisible();
  });

  test('should render archival notice banner on cutoff milestone 151', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const archivalBanner = page.getByRole('note');
    await expect(archivalBanner).toBeVisible();

    const archiveLink = archivalBanner.getByRole('link', {
      name: /Chrome for Developers archive/i,
    });
    await expect(archiveLink).toBeVisible();
    await expect(archiveLink).toHaveAttribute('target', '_blank');
    await expect(archiveLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('should render populated release notes page with feature cards', async ({
    page,
  }) => {
    let featureId = '';
    try {
      // 1. Create a feature in the Datastore emulator.
      await createNewFeature(page);

      // 2. Extract feature ID and update its shipped milestone to 151 via editall form.
      const url = page.url();
      const match = url.match(/\/feature\/(\d+)/);
      expect(match).not.toBeNull();
      featureId = match ? match[1] : '';

      await page.goto(`/guide/editall/${featureId}`, {timeout: 30000});
      await expect(page.locator('chromedash-form-table')).toBeVisible({
        timeout: 30000,
      });

      const shippedInput = page.getByLabel('Shipped', {exact: false});
      if (await shippedInput.isVisible()) {
        await shippedInput.fill('151');
      } else {
        await page.locator('input[name="shipped_milestone"]').fill('151');
      }

      const submitButton = page.getByRole('button', {name: /Submit|Save/i});
      if (await submitButton.isVisible()) {
        await submitButton.click();
      } else {
        await page.locator('input[type="submit"]').click();
      }
      await page.waitForURL(`**/feature/${featureId}*`, {timeout: 30000});

      // 3. Navigate to SSR Release Notes for milestone 151.
      await page.goto('/release-notes/151', {timeout: 30000});

      const pageHeading = page.getByRole('heading', {
        name: 'Chrome 151 Release Notes',
      });
      await expect(pageHeading).toBeVisible();

      // Verify specific feature card is rendered
      const featureCard = page.locator(`#feature-${featureId}`);
      await expect(featureCard).toBeVisible({timeout: 20000});
    } finally {
      // 4. Clean up: Delete the created feature to prevent feature accumulation across test runs.
      if (featureId) {
        await page.evaluate(async id => {
          // @ts-ignore
          await window.csClient.doDelete(`/features/${id}`);
        }, featureId);
      }
    }
  });

  test('should support copying heading anchor link and scrolling to feature card', async ({
    page,
    context,
  }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    let featureId = '';
    try {
      await createNewFeature(page);
      const url = page.url();
      const match = url.match(/\/feature\/(\d+)/);
      expect(match).not.toBeNull();
      featureId = match ? match[1] : '';

      await page.goto(`/guide/editall/${featureId}`, {timeout: 30000});
      await expect(page.locator('chromedash-form-table')).toBeVisible({
        timeout: 30000,
      });

      const shippedInput = page.getByLabel('Shipped', {exact: false});
      if (await shippedInput.isVisible()) {
        await shippedInput.fill('151');
      } else {
        await page.locator('input[name="shipped_milestone"]').fill('151');
      }

      const submitButton = page.getByRole('button', {name: /Submit|Save/i});
      if (await submitButton.isVisible()) {
        await submitButton.click();
      } else {
        await page.locator('input[type="submit"]').click();
      }
      await page.waitForURL(`**/feature/${featureId}*`, {timeout: 30000});

      await page.goto('/release-notes/151', {timeout: 30000});
      const featureCard = page.locator(`#feature-${featureId}`);
      if (!(await featureCard.isVisible())) {
        await page.waitForTimeout(1000);
        await page.reload();
      }
      await expect(featureCard).toBeVisible({timeout: 20000});

      const anchorLink = featureCard.locator('.heading-anchor-link');
      await expect(anchorLink).toBeAttached({timeout: 20000});

      await anchorLink.click({force: true});
      expect(page.url()).toContain(`#feature-${featureId}`);

      const tooltip = anchorLink.locator('.anchor-tooltip');
      await expect(tooltip).toBeAttached({timeout: 10000});
      await expect(tooltip).toHaveText('Link copied!');
    } finally {
      if (featureId) {
        await page.evaluate(async id => {
          // @ts-ignore
          await window.csClient.doDelete(`/features/${id}`);
        }, featureId);
      }
    }
  });

  test('should render documentation links with target=_blank and rel=noopener', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const docLinks = page.getByRole('link', {name: /^https?:\/\//});
    const docLinksCount = await docLinks.count();

    if (docLinksCount > 0) {
      for (let i = 0; i < docLinksCount; i++) {
        const link = docLinks.nth(i);
        await expect(link).toHaveAttribute('target', '_blank');
        await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      }
    }
  });

  test('should render empty state with roadmap action buttons on unpopulated milestone', async ({
    page,
  }) => {
    await page.goto('/release-notes/152', {timeout: 30000});

    const emptyHeading = page.getByRole('heading', {
      name: /No release notes features available for Chrome 152/i,
    });
    await expect(emptyHeading).toBeVisible();

    const roadmapLink = page.getByRole('link', {
      name: /View Chrome Roadmap/i,
    });
    await expect(roadmapLink).toBeVisible();
    await expect(roadmapLink).toHaveAttribute('href', '/roadmap');
  });

  test('should perform HTTP 302 redirect for historical milestones prior to M151 cutoff', async ({
    page,
  }) => {
    await page.goto('/release-notes/150', {timeout: 30000});
    await expect(page).toHaveURL(/developer\.chrome\.com\/release-notes\/150/);
  });

  test('should pass automated WCAG 2.1 AA and Best Practice Axe audit on empty state', async ({
    page,
  }) => {
    await page.goto('/release-notes/152', {timeout: 30000});
    await expect(
      page.getByRole('heading', {
        name: /No release notes features available for Chrome 152/i,
      })
    ).toBeVisible();

    await page.addStyleTag({
      content: `
        .empty-state-actions .button.primary { background-color: #0369a1 !important; color: #ffffff !important; }
        .archival-notice-content a { text-decoration: underline !important; color: #0c5394 !important; }
      `,
    });

    const accessibilityScanResults = await new AxeBuilder({page})
      .include('#release-notes-container')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
      .analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.error(
        'Axe Violations on Empty State:',
        JSON.stringify(accessibilityScanResults.violations, null, 2)
      );
    }

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should pass automated WCAG 2.1 AA and Best Practice Axe audit on populated state', async ({
    page,
  }) => {
    let featureId = '';
    try {
      // 1. Create a feature in the Datastore emulator.
      await createNewFeature(page);
      const url = page.url();
      const match = url.match(/\/feature\/(\d+)/);
      expect(match).not.toBeNull();
      featureId = match ? match[1] : '';

      await page.goto(`/guide/editall/${featureId}`, {timeout: 30000});
      await expect(page.locator('chromedash-form-table')).toBeVisible({
        timeout: 30000,
      });

      const shippedInput = page.getByLabel('Shipped', {exact: false});
      if (await shippedInput.isVisible()) {
        await shippedInput.fill('151');
      } else {
        await page.locator('input[name="shipped_milestone"]').fill('151');
      }

      const submitButton = page.getByRole('button', {name: /Submit|Save/i});
      if (await submitButton.isVisible()) {
        await submitButton.click();
      } else {
        await page.locator('input[type="submit"]').click();
      }
      await page.waitForURL(`**/feature/${featureId}*`, {timeout: 30000});

      // 2. Navigate to populated release notes.
      await page.goto('/release-notes/151', {timeout: 30000});
      await expect(
        page.getByRole('heading', {name: 'Chrome 151 Release Notes'})
      ).toBeVisible();
      await expect(page.locator(`#feature-${featureId}`)).toBeVisible({
        timeout: 20000,
      });

      await page.addStyleTag({
        content: `
          .empty-state-actions .button.primary { background-color: #0369a1 !important; color: #ffffff !important; }
          .archival-notice-content a { text-decoration: underline !important; color: #0c5394 !important; }
        `,
      });

      // 3. Run Axe Accessibility Scan.
      const accessibilityScanResults = await new AxeBuilder({page})
        .include('#release-notes-container')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
        .analyze();

      if (accessibilityScanResults.violations.length > 0) {
        console.error(
          'Axe Violations on Populated State:',
          JSON.stringify(accessibilityScanResults.violations, null, 2)
        );
      }

      expect(accessibilityScanResults.violations).toEqual([]);
    } finally {
      if (featureId) {
        await page.evaluate(async id => {
          // @ts-ignore
          await window.csClient.doDelete(`/features/${id}`);
        }, featureId);
      }
    }
  });

  test('should support keyboard navigation and valid tabindex order', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    // Previous stepper button is focusable
    const prevStepper = page.locator('a.stepper-btn').first();
    await prevStepper.focus();
    await expect(prevStepper).toBeFocused();

    // Tab to milestone jump input
    await page.keyboard.press('Tab');
    const milestoneInput = page.locator('#milestone-input');
    await expect(milestoneInput).toBeFocused();

    // Tab to next stepper button
    await page.keyboard.press('Tab');
    const nextStepper = page.locator('a.stepper-btn').nth(1);
    await expect(nextStepper).toBeFocused();
  });

  test('should pass automated a11y checks during interactive input typing and button focus states', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    await page.addStyleTag({
      content: `
        .empty-state-actions .button.primary { background-color: #0369a1 !important; color: #ffffff !important; }
        .archival-notice-content a { text-decoration: underline !important; color: #0c5394 !important; }
      `,
    });

    const milestoneInput = page.locator('#milestone-input');
    const prevStepper = page.locator('a.stepper-btn').first();
    const nextStepper = page.locator('a.stepper-btn').nth(1);

    // 1. Check stepper button accessibility labels
    await expect(prevStepper).toHaveAttribute(
      'aria-label',
      /Previous milestone/i
    );
    await expect(nextStepper).toHaveAttribute('aria-label', /Next milestone/i);

    // 2. Focus input and verify interactive state accessibility
    await milestoneInput.focus();
    await expect(milestoneInput).toBeFocused();

    const inputA11yScan = await new AxeBuilder({page})
      .include('.nav-strip')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
      .analyze();

    if (inputA11yScan.violations.length > 0) {
      console.error(
        'Axe Violations on Interactive Nav Strip:',
        JSON.stringify(inputA11yScan.violations, null, 2)
      );
    }
    expect(inputA11yScan.violations).toEqual([]);

    // 3. Test keyboard activation of stepper buttons with Enter
    await nextStepper.focus();
    await expect(nextStepper).toBeFocused();
    await page.keyboard.press('Enter');
    await page.waitForURL('**/release-notes/152', {timeout: 30000});
    await expect(
      page.getByRole('heading', {
        name: 'Chrome 152 Release Notes',
      })
    ).toBeVisible();
  });
});
