// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, acceptBeforeUnloadDialogs, delay, login, logout, createNewFeature } from './test_utils';


test.beforeEach(async ({ page }) => {
    captureConsoleMessages(page);
    test.setTimeout(90000);

    // Login before running each test.
    await login(page);
    await acceptBeforeUnloadDialogs(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});


test('edit feature', async ({ page }) => {
    await createNewFeature(page);

    // Edit the feature.
    const editButton = page.locator('a[class="editfeature"]');
    await editButton.click();
    await delay(500);

    // Screenshot editor page
    await expect(page).toHaveScreenshot('new-feature-edit.png');

    // The following causes flakey errors.
    // // Register to accept the confirm dialog before clicking to delete.
    // page.once('dialog', dialog => dialog.accept());

    //   // Delete the new feature.
    // const deleteButton = page.locator('a[id$="delete-feature"]');
    // await deleteButton.click();
    // await delay(500);

    // Screenshot the feature list after deletion.
    // Not yet, since deletion only marks the feature as deleted,
    // and the resulting page is always different.
    // await expect(page).toHaveScreenshot('new-feature-deleted.png');
    // await delay(500);
});
