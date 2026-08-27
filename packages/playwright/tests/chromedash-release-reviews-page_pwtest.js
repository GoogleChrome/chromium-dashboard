// @ts-check
import {expect, test} from '@playwright/test';
import {captureConsoleMessages, isMobile} from './test_utils';

const API_PREFIX = ")]}'\n";

const MOCK_USER = {
  id: 1,
  can_create_feature: true,
  can_edit_all: true,
  can_review_release_notes: true,
  can_comment: true,
  is_admin: true,
  email: 'reviewer@google.com',
  is_site_editor: true,
  approvable_gate_types: [],
  editable_features: [],
};

const MOCK_PENDING_SUGGESTIONS = [
  {
    feature_id: 101,
    feature_name: 'CSS Grid Subgrid',
    status: 'PENDING',
    suggested_summary:
      'Enables nested grid items to align with parent grid tracks.',
    original_summary: 'Subgrid support for CSS Grid layout.',
    suggested_doc_links: [
      {
        url: 'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
        type: 'DOC',
        title: 'MDN Subgrid Guide',
      },
    ],
    version_token: 1,
    created: '2026-08-01T00:00:00Z',
    updated: '2026-08-01T00:00:00Z',
  },
  {
    feature_id: 102,
    feature_name: 'Popover API',
    status: 'PENDING',
    suggested_summary:
      'Provides a declarative mechanism to display top-layer popover content.',
    original_summary: 'HTML Popover attribute support.',
    suggested_doc_links: [],
    version_token: 1,
    created: '2026-08-01T00:00:00Z',
    updated: '2026-08-01T00:00:00Z',
  },
];

test.beforeEach(async ({page}) => {
  captureConsoleMessages(page);

  // Mock permissions endpoint returning reviewer user
  await page.route('**/api/v0/currentuser/permissions*', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: API_PREFIX + JSON.stringify({user: MOCK_USER}),
    });
  });

  // Mock XSRF token for mutations
  await page.route('**/api/v0/currentuser/token', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body:
        API_PREFIX +
        JSON.stringify({
          token: 'mock-xsrf-token',
          token_expires_sec: Math.floor(Date.now() / 1000) + 3600,
        }),
    });
  });

  // Mock user stars
  await page.route('**/api/v0/currentuser/stars', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: API_PREFIX + JSON.stringify([]),
    });
  });

  // Mock pending suggestions queue list (matching only queue endpoints, not pending-count)
  await page.route(
    url =>
      url.pathname === '/api/v0/summary-suggestions/pending' ||
      url.pathname.startsWith('/api/v0/summary-suggestions/pending?'),
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body:
          API_PREFIX +
          JSON.stringify({
            suggestions: MOCK_PENDING_SUGGESTIONS,
            total_count: 2,
            next_cursor: null,
          }),
      });
    }
  );

  // Mock pending suggestions count endpoint specifically
  await page.route(
    url => url.pathname === '/api/v0/summary-suggestions/pending-count',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: API_PREFIX + JSON.stringify({count: 2}),
      });
    }
  );
});

test('Navigation drawer shows Review Release Notes link with count badge', async ({
  page,
}) => {
  await page.goto('/features');

  // Open drawer if on mobile viewport
  if (await isMobile(page)) {
    const menuButton = page.getByTestId('menu');
    await expect(menuButton).toBeVisible();
    await menuButton.click();
  }

  // Verify the Review Release Notes link and badge in drawer
  const reviewLink = page.locator(
    'chromedash-drawer a[href="/review-release-notes"]'
  );
  await expect(reviewLink).toBeVisible();
  await expect(reviewLink).toContainText('Review release notes');

  const reviewBadge = reviewLink.locator('sl-badge');
  await expect(reviewBadge).toBeVisible();
  await expect(reviewBadge).toContainText('2');

  // Click nav link and verify SPA route navigation
  await reviewLink.click();
  await expect(page).toHaveURL(/.*\/review-release-notes/);
  await expect(page.locator('chromedash-release-reviews-page')).toBeVisible();
});

test('Review queue renders cards and opens review dialog', async ({page}) => {
  await page.goto('/review-release-notes');

  const queuePage = page.locator('chromedash-release-reviews-page');
  await expect(queuePage).toBeVisible();

  // Header and count badge
  await expect(queuePage.locator('h1')).toContainText(
    'Release Notes Review Queue'
  );
  await expect(queuePage.locator('.header-left sl-badge')).toContainText('2');

  // Verify card items
  const card101 = queuePage.locator('[data-testid="queue-item-101"]');
  await expect(card101).toBeVisible();
  await expect(card101).toContainText('CSS Grid Subgrid');
  await expect(card101).toContainText(
    'Enables nested grid items to align with parent grid tracks.'
  );

  const card102 = queuePage.locator('[data-testid="queue-item-102"]');
  await expect(card102).toBeVisible();
  await expect(card102).toContainText('Popover API');

  // Click Review suggestion button on card 101
  const reviewButton = queuePage.locator('[data-testid="review-button-101"]');
  await expect(reviewButton).toBeVisible();
  await reviewButton.click();

  // Verify dialog opened
  const slDialog = queuePage.locator(
    'chromedash-summary-review-dialog sl-dialog'
  );
  await expect(slDialog).toHaveAttribute('open', '');
  await expect(slDialog).toContainText('Review AI Summary Suggestion');
  await expect(slDialog).toContainText('Subgrid support for CSS Grid layout.');
  await expect(slDialog).toContainText(
    'Enables nested grid items to align with parent grid tracks.'
  );
});

test('Applying suggestion removes card from queue in real-time', async ({
  page,
}) => {
  // Mock PATCH apply endpoint
  await page.route('**/api/v0/summary-suggestions/101', async route => {
    if (route.request().method() === 'PATCH') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body:
          API_PREFIX +
          JSON.stringify({
            suggestion: {
              ...MOCK_PENDING_SUGGESTIONS[0],
              status: 'APPLIED',
              version_token: 2,
            },
            progress_steps: [],
          }),
      });
    } else {
      await route.fallback();
    }
  });

  await page.goto('/review-release-notes');

  const queuePage = page.locator('chromedash-release-reviews-page');
  const card101 = queuePage.locator('[data-testid="queue-item-101"]');
  await expect(card101).toBeVisible();

  // Open review dialog
  await queuePage.locator('[data-testid="review-button-101"]').click();

  const slDialog = queuePage.locator(
    'chromedash-summary-review-dialog sl-dialog'
  );
  await expect(slDialog).toHaveAttribute('open', '');

  // Click Accept & Apply button in modal footer
  const applyButton = queuePage.locator(
    'chromedash-summary-review-dialog sl-button[variant="primary"]'
  );
  await expect(applyButton).toBeVisible();
  await applyButton.click();

  // Assert card 101 is removed from queue in DOM and total count decrements
  await expect(card101).not.toBeVisible();
  await expect(
    queuePage.locator('[data-testid="queue-item-102"]')
  ).toBeVisible();
  await expect(queuePage.locator('.header-left sl-badge')).toContainText('1');
});

test('Empty state renders when no pending suggestions exist', async ({
  page,
}) => {
  // Override queue with empty list
  await page.route(
    url =>
      url.pathname === '/api/v0/summary-suggestions/pending' ||
      url.pathname.startsWith('/api/v0/summary-suggestions/pending?'),
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body:
          API_PREFIX +
          JSON.stringify({
            suggestions: [],
            total_count: 0,
            next_cursor: null,
          }),
      });
    }
  );

  await page.route(
    url => url.pathname === '/api/v0/summary-suggestions/pending-count',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: API_PREFIX + JSON.stringify({count: 0}),
      });
    }
  );

  await page.goto('/review-release-notes');

  const queuePage = page.locator('chromedash-release-reviews-page');
  await expect(queuePage.locator('.empty-state')).toBeVisible();
  await expect(queuePage.locator('.empty-state')).toContainText(
    'All caught up!'
  );
  await expect(queuePage.locator('.header-left sl-badge')).toContainText('0');
});
