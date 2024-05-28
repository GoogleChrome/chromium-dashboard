// @ts-check
import {expect, test} from '@playwright/test';

test('new features page link is clickable while features are loading', async ({
  page,
}) => {
  let resolveFeatures = _ => {};
  const featuresMayResolve = new Promise(resolve => {
    resolveFeatures = resolve;
  });
  await page.route('/features_v2.json', async route => {
    // Hang until the test says to resolve the request.
    route.fulfill({
      status: 200,
      body: `)]}'\n${JSON.stringify(await featuresMayResolve)}`,
    });
  });
  await page.goto('/features');
  const newFeaturesLocator = page.getByRole('link', {
    name: 'Try out our new features page',
  });
  await expect(newFeaturesLocator).toBeVisible();
  await newFeaturesLocator.click({timeout: 5000});
  await expect(page).toHaveURL('/newfeatures');

  // Don't leave the network request hanging forever.
  resolveFeatures({});
});
