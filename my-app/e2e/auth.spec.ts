import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

/**
 * Flow 2 — Auth (sign-up / log-in screens, unauthenticated redirect guard)
 *
 * MediSage does not perform a hard redirect away from /diagnosis for
 * unauthenticated users — the page renders but the workflow requires a
 * logged-in session cookie for API calls.  We therefore test:
 *   1. The login page renders correctly.
 *   2. The register page renders correctly.
 *   3. Bad credentials surface an error message (mocked).
 *   4. The navbar on the homepage shows a "Login" link when not logged in.
 */

test.describe('Flow 2 — Auth screens', () => {

  test('login page renders all required form elements', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('h2', { hasText: 'Login' })).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    // Link to register page
    await expect(page.locator('a[href="/register"]')).toBeVisible();

    await page.screenshot({ path: `${SCREENSHOT_DIR}/07-login-form.png` });
  });

  test('register page renders all required form elements', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');

    // Title
    await expect(page.locator('h2').first()).toBeVisible();
    // At minimum email + password inputs
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
    // Submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    await page.screenshot({ path: `${SCREENSHOT_DIR}/08-register-form.png` });
  });

  test('invalid login credentials show an error message', async ({ page }) => {
    // Intercept the profile check (auth context) and the login POST
    await page.route('**/auth/patient/profile', async route => {
      await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) });
    });
    await page.route('**/auth/patient/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      });
    });

    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('badpassword');
    await page.locator('button[type="submit"]').click();

    // An error paragraph should appear
    await expect(
      page.locator('p').filter({ hasText: /invalid|error|incorrect|failed/i }).first()
    ).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/09-login-error.png` });
  });

  test('homepage navbar shows Login link when user is not logged in', async ({ page }) => {
    // Stub profile to 401 so AuthContext resolves as logged-out
    await page.route('**/auth/patient/profile', async route => {
      await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) });
    });

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Navbar shows a Login button (styled button, not an anchor) when logged out
    await expect(page.locator('button:has-text("Login")')).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/10-navbar-logged-out.png` });
  });

  test('navigating to /diagnosis while logged out still renders the page (no hard redirect)', async ({ page }) => {
    await page.route('**/auth/patient/profile', async route => {
      await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    // Should remain on /diagnosis — not redirected to /login
    expect(page.url()).toContain('/diagnosis');
    // The symptom input form should be present
    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/11-diagnosis-unauth.png` });
  });
});
