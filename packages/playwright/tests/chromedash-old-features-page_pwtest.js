// @ts-check
import {errors, expect, test} from '@playwright/test';

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
  await page.goto('/oldfeatures');
  const newFeaturesLocator = page.getByRole('link', {
    name: 'Try out our new features page',
  });
  await expect(newFeaturesLocator).toBeVisible();
  try {
    await newFeaturesLocator.click({timeout: 500});
  } catch (e) {
    const signInDialogLocator = page.getByTitle('Sign in with Google Dialog');
    // If this is a timeout because the Google sign-in dialog is present.
    if (
      e instanceof errors.TimeoutError &&
      (await signInDialogLocator?.isVisible())
    ) {
      // Dismiss the dialog.
      await signInDialogLocator.press('Escape');
      // And retry the click.
      await newFeaturesLocator.click({timeout: 5000});
    } else {
      throw e;
    }
  }
  await expect(page).toHaveURL('/features');

  // Don't leave the network request hanging forever.
  resolveFeatures({});
});
