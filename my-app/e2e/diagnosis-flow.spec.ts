import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

/**
 * Flow 3 — Full diagnosis workflow (mocked backend)
 *
 * All API calls are intercepted so the test is deterministic and
 * does not require a live Groq/Supabase session.
 *
 * Workflow stages exercised:
 *   textual_analysis  →  awaiting_followup_responses  →
 *   followup_analysis_complete  →  overall_analysis_complete  →
 *   workflow_complete
 */

// ---------------------------------------------------------------------------
// Shared mock payloads
// ---------------------------------------------------------------------------

const TEXTUAL_ANALYSIS_RESPONSE = {
  session_id: 'test-session-001',
  result: {
    current_workflow_stage: 'textual_analysis_complete',
    textual_analysis: [
      {
        text_diagnosis: 'Tension Headache',
        diagnosis_confidence: 0.82,
        diagnosis_description: 'Likely tension-type headache with fatigue.',
      },
    ],
    average_confidence: 0.82,
    image_required: false,
    requires_user_input: false,
    workflow_path: ['textual_analysis'],
    skin_cancer_risk_detected: false,
    followup_questions: [],
    followup_diagnosis: [],
    overall_analysis: null,
    medical_report: null,
  },
  workflow_info: {
    next_endpoint: null,
    needs_user_input: 'followup_questions',
    workflow_complete: false,
    next_step_description: 'Generate follow-up questions',
  },
};

const FOLLOWUP_QUESTIONS_RESPONSE = {
  session_id: 'test-session-001',
  result: {
    ...TEXTUAL_ANALYSIS_RESPONSE.result,
    current_workflow_stage: 'awaiting_followup_responses',
    followup_questions: [
      'How long have you had the headache?',
      'Rate your pain from 1 to 10.',
    ],
    requires_user_input: true,
  },
  workflow_info: {
    next_endpoint: null,
    needs_user_input: 'followup_questions',
    workflow_complete: false,
    next_step_description: 'Awaiting user responses',
  },
};

const FOLLOWUP_SUBMIT_RESPONSE = {
  session_id: 'test-session-001',
  result: {
    ...TEXTUAL_ANALYSIS_RESPONSE.result,
    current_workflow_stage: 'followup_analysis_complete',
    followup_diagnosis: [
      {
        text_diagnosis: 'Tension Headache (confirmed)',
        diagnosis_confidence: 0.88,
        diagnosis_description: 'Follow-up confirms tension-type headache.',
      },
    ],
    requires_user_input: false,
  },
  workflow_info: {
    next_endpoint: '/patient/overall_analysis',
    needs_user_input: null,
    workflow_complete: false,
    next_step_description: 'Proceed to overall analysis',
  },
};

const OVERALL_ANALYSIS_RESPONSE = {
  session_id: 'test-session-001',
  result: {
    ...TEXTUAL_ANALYSIS_RESPONSE.result,
    current_workflow_stage: 'overall_analysis_complete',
    overall_analysis: 'Patient likely has a tension headache. Recommend rest and hydration.',
    requires_user_input: false,
  },
  workflow_info: {
    next_endpoint: '/patient/medical_report',
    needs_user_input: null,
    workflow_complete: false,
    next_step_description: 'Generate medical report',
  },
};

const MEDICAL_REPORT_RESPONSE = {
  session_id: 'test-session-001',
  result: {
    ...TEXTUAL_ANALYSIS_RESPONSE.result,
    current_workflow_stage: 'workflow_complete',
    medical_report: {
      summary: 'Tension headache diagnosis.',
      recommendations: ['Rest', 'Hydrate', 'Avoid screen time'],
      generated_at: '2026-06-09T12:00:00Z',
    },
    requires_user_input: false,
  },
  workflow_info: {
    next_endpoint: null,
    needs_user_input: null,
    workflow_complete: true,
    next_step_description: 'Workflow complete',
  },
};

// ---------------------------------------------------------------------------
// Helper: register all API mocks
// ---------------------------------------------------------------------------

async function setupMocks(page: import('@playwright/test').Page) {
  // Auth — always logged in. Glob handles repeated calls (re-mount triggers new fetch).
  await page.route('**/auth/patient/profile', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'user-1', email: 'test@medisage.test', privacy_policy_accepted: true }),
    });
  });

  await page.route('http://localhost:8000/auth/accept-privacy-policy', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });

  await page.route('http://localhost:8000/patient/followup_questions', async route => {
    const body = route.request().postData() ?? '';
    if (body.includes('followup_responses')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(FOLLOWUP_SUBMIT_RESPONSE),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(FOLLOWUP_QUESTIONS_RESPONSE),
      });
    }
  });

  await page.route('http://localhost:8000/patient/textual_analysis', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(TEXTUAL_ANALYSIS_RESPONSE),
    });
  });

  await page.route('http://localhost:8000/patient/overall_analysis', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(OVERALL_ANALYSIS_RESPONSE),
    });
  });

  await page.route('http://localhost:8000/patient/medical_report', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MEDICAL_REPORT_RESPONSE),
    });
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Flow 3 — Diagnosis workflow (mocked)', () => {

  test('step 1: symptom form is present and accepts input', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });

    await textarea.fill('I have a mild headache and feel tired');
    await expect(textarea).toHaveValue('I have a mild headache and feel tired');

    await page.screenshot({ path: `${SCREENSHOT_DIR}/12-symptom-form-filled.png` });
  });

  test('step 2: submitting symptoms shows initial analysis results', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    await page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first().click();

    // The DiagnosisFormPage should now show analysis results
    await expect(
      page.locator('text=Tension Headache').or(page.locator('text=Initial Analysis')).first()
    ).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/13-initial-analysis.png` });
  });

  test('step 3: continuing from initial analysis generates follow-up questions', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/diagnosis');
    // domcontentloaded avoids hanging on Vite HMR websocket (never reaches networkidle)
    await page.waitForLoadState('domcontentloaded');

    // Submit symptoms
    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    const [_analysisResp] = await Promise.all([
      page.waitForResponse('http://localhost:8000/patient/textual_analysis'),
      page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first().click(),
    ]);

    // Initial analysis results must be visible
    await expect(
      page.locator('text=Tension Headache').or(page.locator('text=Initial Analysis')).first()
    ).toBeVisible({ timeout: 10000 });

    // Scroll Continue button into view then click, waiting for the followup API call
    const continueBtn = page.locator('button:has-text("Continue")').first();
    await continueBtn.scrollIntoViewIfNeeded();
    await expect(continueBtn).toBeVisible({ timeout: 6000 });
    const [_followupResp] = await Promise.all([
      page.waitForResponse('http://localhost:8000/patient/followup_questions'),
      continueBtn.click(),
    ]);

    // FollowUpQuestionsPage renders with this PageHeader title
    await expect(page.locator('text=Follow-Up Questions')).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/14-followup-questions.png` });
  });

  test('step 4: answering follow-up questions and submitting proceeds to analysis', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/diagnosis');
    await page.waitForLoadState('domcontentloaded');

    // Submit symptoms
    const textarea = page.locator('textarea, [placeholder*="symptom" i], [placeholder*="describe" i]').first();
    await expect(textarea).toBeVisible({ timeout: 8000 });
    await textarea.fill('I have a mild headache and feel tired');

    const [_analysisResp] = await Promise.all([
      page.waitForResponse('http://localhost:8000/patient/textual_analysis'),
      page.locator('button[type="submit"], button:has-text("Start AI Diagnosis")').first().click(),
    ]);

    // Wait for initial results
    await expect(
      page.locator('text=Tension Headache').or(page.locator('text=Initial Analysis')).first()
    ).toBeVisible({ timeout: 10000 });

    // Click Continue and wait for the follow-up questions API call
    const continueBtn = page.locator('button:has-text("Continue")').first();
    await continueBtn.scrollIntoViewIfNeeded();
    const [_followupResp] = await Promise.all([
      page.waitForResponse('http://localhost:8000/patient/followup_questions'),
      continueBtn.click(),
    ]);

    // Wait for FollowUpQuestionsPage
    await expect(page.locator('text=Follow-Up Questions')).toBeVisible({ timeout: 10000 });

    // Fill in all text inputs in the follow-up form
    const inputs = page.locator('input[type="text"], textarea').filter({ hasNot: page.locator('[placeholder*="symptom" i]') });
    const count = await inputs.count();
    for (let i = 0; i < count; i++) {
      await inputs.nth(i).fill('About 2 days, pain level 4');
    }

    // Submit follow-up and wait for the submission + overall analysis + report calls
    const submitBtn = page.locator('button[type="submit"], button:has-text("Submit")').last();
    await submitBtn.scrollIntoViewIfNeeded();
    await submitBtn.click();

    // After follow-up the workflow auto-progresses to the final report
    await expect(
      page.locator('text=Final Medical Report')
        .or(page.locator('text=Overall Analysis'))
        .first()
    ).toBeVisible({ timeout: 20000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/15-after-followup.png` });
  });
});
