import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

/**
 * Flow 1 — Privacy Policy Gate
 *
 * The privacy-policy modal is shown when a user tries to start a diagnosis
 * (the backend returns 403 with detail=privacy_policy_required).  The modal
 * does NOT appear on the homepage or the login page; it surfaces only when
 * the /patient/textual_analysis endpoint is called without a prior
 * acceptPrivacyPolicy call.
 *
 * We therefore test:
 *   1. Navigating to the root — homepage loads without any modal.
 *   2. Navigating to /login  — login form is visible.
 *   3. Navigating to /diagnosis — the page renders (the WorkflowRouter
 *      shows the DiagnosisForm); the privacy modal is NOT shown until the
 *      user actually tries to submit symptoms and gets the 403 back.
 *   4. Submitting symptoms while not logged in triggers the privacy modal
 *      (backend returns 403 → frontend shows the modal).
 *   5. Clicking "Accept & Continue" dismisses the modal.
 *   6. Clicking "Cancel"  also dismisses the modal without proceeding.
 */

test.describe('Flow 1 — Privacy policy gate', () => {

  test('homepage loads — no privacy modal on landing', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // The privacy modal overlay should not be present on the homepage
    const overlay = page.locator('text=Data Privacy Notice');
    await expect(overlay).not.toBeVisible();

    // The page should have meaningful content (hero / nav)
    await expect(page).toHaveTitle(/MediSage/i);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/01-homepage.png` });
  });

  test('login page is reachable and shows the login form', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('h2', { hasText: 'Login' })).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();

    await page.screenshot({ path: `${SCREENSHOT_DIR}/02-login-page.png` });
  });

  test('diagnosis page renders the symptom form for unauthenticated users', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    // The WorkflowRouter defaults to DiagnosisFormPage when no workflow state exists.
    // The symptom textarea / submit button should be visible.
    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/03-diagnosis-form.png` });
  });

  test('submitting symptoms triggers privacy-policy modal (403 gate)', async ({ page }) => {
    // Intercept the textual_analysis POST and return the 403 privacy gate response
    // so the test is backend-independent and deterministic.
    await page.route('**/patient/textual_analysis', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'privacy_policy_required' }),
      });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    const submitBtn = page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first();
    await submitBtn.click();

    // The frontend should detect the 403 and surface the privacy modal
    await expect(page.locator('text=Data Privacy Notice')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('button:has-text("Accept & Continue")')).toBeVisible();
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();

    await page.screenshot({ path: `${SCREENSHOT_DIR}/04-privacy-modal-visible.png` });
  });

  test('clicking Cancel dismisses the privacy modal', async ({ page }) => {
    await page.route('**/patient/textual_analysis', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'privacy_policy_required' }),
      });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    await page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first().click();
    await expect(page.locator('text=Data Privacy Notice')).toBeVisible({ timeout: 8000 });

    // Click Cancel
    await page.locator('button:has-text("Cancel")').click();
    await expect(page.locator('text=Data Privacy Notice')).not.toBeVisible({ timeout: 4000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/05-modal-dismissed.png` });
  });

  test('clicking Accept & Continue calls acceptPrivacyPolicy endpoint', async ({ page }) => {
    let privacyAcceptCalled = false;

    await page.route('**/patient/textual_analysis', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'privacy_policy_required' }),
      });
    });

    await page.route('**/auth/accept-privacy-policy', async route => {
      privacyAcceptCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ accepted: true }),
      });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    await page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first().click();
    await expect(page.locator('text=Data Privacy Notice')).toBeVisible({ timeout: 8000 });

    await page.locator('button:has-text("Accept & Continue")').click();

    // The accept endpoint must have been called
    await page.waitForTimeout(1500);
    expect(privacyAcceptCalled).toBe(true);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/06-after-accept.png` });
  });
});
