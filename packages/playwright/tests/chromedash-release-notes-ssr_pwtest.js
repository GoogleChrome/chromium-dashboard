// @ts-check
import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
  trackCumulativeLayoutShift,
  expectZeroLayoutShift,
} from './test_utils';

const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'];

/**
 * Shared helper to create a feature in the Datastore emulator,
 * assign its shipped milestone, run test assertions, and ensure clean teardown.
 * @param {import('@playwright/test').Page} page
 * @param {number|string} milestone
 * @param {(featureId: string) => Promise<void>} testFn
 */
async function withShippedFeature(page, milestone, testFn) {
  let featureId = '';
  try {
    await createNewFeature(page);

    const match = page.url().match(/\/feature\/(\d+)/);
    expect(match).not.toBeNull();
    featureId = match ? match[1] : '';

    const editButton = page.locator('a[href^="/guide/editall/"]');
    await expect(editButton).toBeVisible({timeout: 15000});
    await editButton.click();

    await expect(page.locator('chromedash-form-table')).toBeVisible({
      timeout: 30000,
    });

    const shippedInput = page.locator('input[name="shipped_milestone"]');
    await expect(shippedInput).toBeVisible({timeout: 10000});
    await shippedInput.fill(String(milestone));

    const submitButton = page.locator('input[type="submit"]');
    await submitButton.click();

    await page.waitForURL(new RegExp(`/feature/${featureId}`), {
      timeout: 30000,
    });
    await expect(page.locator('chromedash-feature-detail')).toBeVisible({
      timeout: 30000,
    });

    await testFn(featureId);
  } finally {
    if (featureId) {
      await page
        .evaluate(async id => {
          const client = window['csClient'];
          if (client) await client.doDelete(`/features/${id}`);
        }, featureId)
        .catch(() => {});
    }
  }
}

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
    await trackCumulativeLayoutShift(page);
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
    const option151 = page
      .locator('#milestones-datalist')
      .locator('option[value="Chrome 151"]');
    await expect(option151).toBeAttached();

    await expectZeroLayoutShift(page);
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

    await expect(page).toHaveURL(/\/release-notes\/152/);
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

    // Select/fill formatted milestone string and press Enter to trigger change
    await jumpInput.fill('Chrome 153');
    await jumpInput.press('Enter');

    await expect(page).toHaveURL(/\/release-notes\/153/);
    const newHeading = page.getByRole('heading', {
      name: 'Chrome 153 Release Notes',
    });
    await expect(newHeading).toBeVisible();
    await expect(jumpInput).toHaveValue('Chrome 153');
  });

  test('should not navigate when typing numbers below minimum milestone threshold (< 124)', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const jumpInput = page.getByLabel('Jump to Chrome milestone');
    await expect(jumpInput).toBeVisible();

    // Type single leading digit '1' and press Enter - should not navigate
    await jumpInput.fill('1');
    await jumpInput.press('Enter');
    await expect(page).toHaveURL(/\/release-notes\/151/);

    // Type '12' and press Enter - should not navigate
    await jumpInput.fill('12');
    await jumpInput.press('Enter');
    await expect(page).toHaveURL(/\/release-notes\/151/);
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
    await expect(page).toHaveURL(/\/release-notes\/152/);

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
      name: /archive/i,
    });
    await expect(archiveLink).toBeVisible();
    await expect(archiveLink).toHaveAttribute('target', '_blank');
    await expect(archiveLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('should render populated release notes page with feature cards', async ({
    page,
  }) => {
    await withShippedFeature(page, 151, async featureId => {
      await trackCumulativeLayoutShift(page);
      await page.goto('/release-notes/151', {timeout: 30000});

      const pageHeading = page.getByRole('heading', {
        name: 'Chrome 151 Release Notes',
      });
      await expect(pageHeading).toBeVisible();

      // Verify specific feature card is rendered
      const featureCard = page.locator(`#feature-${featureId}`);
      await expect(featureCard).toBeVisible({timeout: 20000});

      // Verify feature title permalink
      const titleLink = featureCard.locator('.feature-name');
      await expect(titleLink).toHaveAttribute('href', `/feature/${featureId}`);

      // Verify metadata links bar
      const linksBar = featureCard.locator('.feature-links-bar');
      await expect(linksBar).toBeVisible();
      const entryLink = linksBar.getByRole('link', {
        name: 'ChromeStatus.com entry',
      });
      await expect(entryLink).toHaveAttribute('href', `/feature/${featureId}`);

      await expectZeroLayoutShift(page);
    });
  });

  test('should support copying heading anchor link and scrolling to feature card', async ({
    page,
    context,
    browserName,
  }) => {
    if (browserName === 'chromium') {
      try {
        await context.grantPermissions(['clipboard-read', 'clipboard-write']);
      } catch {
        // Ignore permission failure in non-supporting contexts
      }
    }

    await withShippedFeature(page, 151, async featureId => {
      await page.goto('/release-notes/151', {timeout: 30000});

      const featureCard = page.locator(`#feature-${featureId}`);
      await expect(featureCard).toBeVisible({timeout: 20000});

      const anchorLink = featureCard.getByRole('link', {
        name: /Copy link to/i,
      });

      // Idiomatic Playwright: Hover over card to reveal CSS-transitioned anchor link
      await featureCard.hover();
      await expect(anchorLink).toBeVisible();
      await anchorLink.click();

      await expect(page).toHaveURL(new RegExp(`#feature-${featureId}$`));

      // Assert tooltip is visually rendered (not just attached in DOM)
      const tooltip = anchorLink.getByRole('status');
      await expect(tooltip).toBeVisible({timeout: 5000});
      await expect(tooltip).toHaveText('Link copied!');
    });
  });

  test('should render external links with target=_blank and rel=noopener', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const archiveLink = page.getByRole('link', {
      name: /archive/i,
    });
    await expect(archiveLink).toBeVisible({timeout: 20000});
    await expect(archiveLink).toHaveAttribute('target', '_blank');
    await expect(archiveLink).toHaveAttribute('rel', 'noopener noreferrer');

    // Verify all documentation links on feature cards enforce safe external window behavior
    const docLinks = page.locator('.feature-doc-links a');
    const docLinkCount = await docLinks.count();
    if (docLinkCount > 0) {
      for (let i = 0; i < docLinkCount; i++) {
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

    // Audit unmodified production CSS directly
    const accessibilityScanResults = await new AxeBuilder({page})
      .include('#release-notes-container')
      .withTags(AXE_TAGS)
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
    await withShippedFeature(page, 151, async featureId => {
      await page.goto('/release-notes/151', {timeout: 30000});
      await expect(
        page.getByRole('heading', {name: 'Chrome 151 Release Notes'})
      ).toBeVisible();
      await expect(page.locator(`#feature-${featureId}`)).toBeVisible({
        timeout: 20000,
      });

      // Audit unmodified production CSS directly
      const accessibilityScanResults = await new AxeBuilder({page})
        .include('#release-notes-container')
        .withTags(AXE_TAGS)
        .analyze();

      if (accessibilityScanResults.violations.length > 0) {
        console.error(
          'Axe Violations on Populated State:',
          JSON.stringify(accessibilityScanResults.violations, null, 2)
        );
      }

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  });

  test('should support keyboard navigation and valid tabindex order', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const prevStepper = page.getByRole('link', {
      name: /Previous milestone: Chrome 150/i,
    });
    const milestoneInput = page.getByLabel('Jump to Chrome milestone');
    const nextStepper = page.getByRole('link', {
      name: /Next milestone: Chrome 152/i,
    });

    // Previous stepper button is focusable
    await prevStepper.focus();
    await expect(prevStepper).toBeFocused();

    // Tab to milestone jump input
    await page.keyboard.press('Tab');
    await expect(milestoneInput).toBeFocused();

    // Tab to next stepper button
    await page.keyboard.press('Tab');
    await expect(nextStepper).toBeFocused();
  });

  test('should pass automated a11y checks during interactive input typing and button focus states', async ({
    page,
  }) => {
    await page.goto('/release-notes/151', {timeout: 30000});

    const milestoneInput = page.getByLabel('Jump to Chrome milestone');
    const prevStepper = page.getByRole('link', {
      name: /Previous milestone: Chrome 150/i,
    });
    const nextStepper = page.getByRole('link', {
      name: /Next milestone: Chrome 152/i,
    });

    // 1. Check stepper button accessibility labels
    await expect(prevStepper).toHaveAttribute(
      'aria-label',
      /Previous milestone/i
    );
    await expect(nextStepper).toHaveAttribute('aria-label', /Next milestone/i);

    // 2. Focus input and verify interactive state accessibility on unmodified styles
    await milestoneInput.focus();
    await expect(milestoneInput).toBeFocused();

    const inputA11yScan = await new AxeBuilder({page})
      .include('.nav-strip')
      .withTags(AXE_TAGS)
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
    await expect(page).toHaveURL(/\/release-notes\/152/);
    await expect(
      page.getByRole('heading', {
        name: 'Chrome 152 Release Notes',
      })
    ).toBeVisible();
  });
});
