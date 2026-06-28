import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

/**
 * Flow 4 — ChatPanel presence and basic interaction
 *
 * The ChatPanel is rendered unconditionally inside diagnosis.tsx, so it is
 * always present on /diagnosis regardless of auth or workflow state.
 */

test.describe('Flow 4 — ChatPanel', () => {

  test.beforeEach(async ({ page }) => {
    // Stub auth so AuthContext resolves quickly
    await page.route('**/auth/patient/profile', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'user-1', email: 'test@medisage.test', privacy_policy_accepted: true }),
      });
    });
  });

  test('ChatPanel renders on the diagnosis page', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    // The ChatPanel header text
    await expect(page.locator('text=Medical History Assistant')).toBeVisible({ timeout: 8000 });

    // The chat input and Send button
    await expect(page.locator('input[placeholder*="medical history" i], input[placeholder*="Ask" i]').first()).toBeVisible({ timeout: 6000 });
    await expect(page.locator('button:has-text("Send")')).toBeVisible({ timeout: 6000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/16-chatpanel-present.png` });
  });

  test('ChatPanel shows default assistant greeting', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    await expect(
      page.locator('text=Ask me anything about your past diagnoses')
    ).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/17-chatpanel-greeting.png` });
  });

  test('ChatPanel Send button is disabled when input is empty', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('button:has-text("Send")')).toBeDisabled({ timeout: 6000 });
  });

  test('ChatPanel Send button enables when user types a message', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const chatInput = page.locator('input[placeholder*="medical history" i], input[placeholder*="Ask" i]').first();
    await expect(chatInput).toBeVisible({ timeout: 8000 });

    await chatInput.fill('What was my last diagnosis?');
    await expect(page.locator('button:has-text("Send")')).toBeEnabled({ timeout: 4000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/18-chatpanel-input-filled.png` });
  });

  test('ChatPanel sends a message and shows a response (mocked)', async ({ page }) => {
    await page.route('**/chat/ask', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: 'Your last diagnosis was a tension headache.',
          sources: ['report-2026-06-09'],
        }),
      });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const chatInput = page.locator('input[placeholder*="medical history" i], input[placeholder*="Ask" i]').first();
    await expect(chatInput).toBeVisible({ timeout: 8000 });

    await chatInput.fill('What was my last diagnosis?');
    await page.locator('button:has-text("Send")').click();

    // User bubble appears
    await expect(page.locator('text=What was my last diagnosis?')).toBeVisible({ timeout: 6000 });

    // Assistant response appears
    await expect(page.locator('text=tension headache')).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/19-chatpanel-response.png` });
  });

  test('ChatPanel shows loading indicator while waiting for response', async ({ page }) => {
    // Delay the mock response by 2 seconds so we can catch the loading state
    await page.route('**/chat/ask', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ answer: 'Here is your answer.', sources: [] }),
      });
    });

    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const chatInput = page.locator('input[placeholder*="medical history" i], input[placeholder*="Ask" i]').first();
    await expect(chatInput).toBeVisible({ timeout: 8000 });

    await chatInput.fill('Tell me about my reports');
    await page.locator('button:has-text("Send")').click();

    // Loading bubble text is "Searching your records..."
    await expect(page.locator('text=Searching your records...')).toBeVisible({ timeout: 4000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/20-chatpanel-loading.png` });
  });
});
