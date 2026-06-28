# MediSage — Legal & Lawsuit-Risk Measures

> Reference for reducing legal exposure of an AI symptom-assessment tool moving toward production.
> **This is engineering documentation, not legal advice.** Before public launch, have a qualified
> lawyer review the Terms of Service, Privacy Policy, and the regulatory questions in Section 4.

Last updated: 12 June 2026

---

## Summary

| # | Measure | Status | Where |
|---|---------|--------|-------|
| 1 | Terms of Service (liability shield) | ✅ In app | [`/terms`](../my-app/src/views/terms.tsx) |
| 2 | Privacy Policy (transparency / GDPR-PDPA) | ✅ In app | [`/privacy`](../my-app/src/views/privacypolicy.tsx) |
| 3 | First-use consent gate (ToS + Privacy + disclaimer) | ✅ In app | [`PrivacyPolicyModal.tsx`](../my-app/src/components/medical/PrivacyPolicyModal.tsx) |
| 4 | Educational / non-medical-device positioning | ⚠️ In-app done; regulatory + legal review outstanding | see §4 |
| 5 | Report-storage consent (explicit save) | ✅ In app | [`FinalReportPage.tsx`](../my-app/src/pages/diagnosis/FinalReportPage.tsx) |
| 6 | Professional legal review | ❌ Outstanding | — |
| 7 | Age-eligibility enforcement | ❌ Stated in ToS, not enforced in code | see §4 |

Legend: ✅ done · ⚠️ partial · ❌ not done

---

## 1. Terms of Service — the liability shield

A Terms of Service is the document that actually limits liability in a dispute (a privacy policy
cannot do this job). The MediSage ToS includes the clauses that matter for a health tool:

- **Not medical advice / no doctor–patient relationship** (§2)
- **Not a certified or registered medical device; not clinically validated** (§2)
- **Not for emergencies** (§3)
- **Assumption of risk** — AI output may be wrong; reliance is at the user's own risk (§6)
- **Disclaimer of warranties** — provided "as is", no warranty of accuracy (§9)
- **Limitation of liability** — excludes indirect/consequential damages to the extent law allows (§10)
- **Indemnification** (§11)
- **Governing law** — Malaysia (§13)

Gate: accepted at first protected use via the consent modal (see §3).

## 2. Privacy Policy — transparency obligation

Required by data-protection law (GDPR for EEA users; Malaysia's PDPA 2010). It is honest about the
**actual** MediSage stack and does **not** copy unverifiable claims (e.g. HIPAA BAAs, ISO 27001,
EU-only servers) that would be false and would *increase* liability. It discloses:

- what data is collected (account, symptom text, optionally-saved reports, auth cookie);
- health data as special-category data under GDPR Art. 9 / PDPA;
- service providers that process data (**Groq** for inference, **Supabase** for auth + storage);
- security, retention, and user rights (access, rectify, delete, withdraw consent);
- that reports are stored only when the user chooses (§2) and that the tool is not medical advice (§8).

**Following the policy is what protects you** — breaching your own stated policy is itself actionable.

## 3. First-use consent gate

One combined gate covers **both** documents and the medical disclaimer — chosen over two separate
modals (redundant, poor UX). A single backend acceptance flag records it.

- **Position — diagnosis workflow:** triggered when the user first submits symptoms (the first
  `require_privacy_policy`-protected call returns HTTP 403 `privacy_policy_required`); handled in
  [`useDiagnosis.ts`](../my-app/src/hooks/useDiagnosis.ts).
- **Position — chatbot:** triggered when the user sends their first chat message; handled in
  [`useChat.ts`](../my-app/src/hooks/useChat.ts). (Previously the chatbot swallowed this error and
  showed no gate — fixed.)
- **Mechanics:** affirmative **checkbox** (links to ToS and Privacy Policy) must be ticked before the
  "Agree & continue" button enables — affirmative action is what GDPR Art. 9 explicit consent requires.
- **Backend:** `require_privacy_policy` dependency + `PATCH /auth/accept-privacy-policy`
  ([`auth_routes.py`](../backend/api/auth_routes.py)). The stored flag is named
  `privacy_policy_accepted`; it now represents acceptance of **both** the ToS and the Privacy Policy.
  *Future cleanup:* rename the column to `terms_accepted_at` (timestamp) for an auditable record of
  *when* and *which version* was accepted — requires a Supabase migration.

## 4. Educational / non-medical-device positioning

### Done (in-app)
- "For educational purposes only / not medical advice / not a diagnosis" on the homepage CTA,
  diagnosis page, final report, consent modal, Privacy Policy §8, and ToS §2.
- Explicit **"not a certified or registered medical device, not clinically validated"** (ToS §2,
  Privacy §8).
- **Emergency red-flag**: critical/emergency severity shows an alert directing the user to emergency
  services ([`FinalReportPage.tsx`](../my-app/src/pages/diagnosis/FinalReportPage.tsx)); ToS §3 reinforces.
- No claims of diagnostic accuracy anywhere (deliberately — unsubstantiated accuracy claims raise risk).

### Outstanding (cannot be solved in code)
1. **Regulatory classification.** Symptom-assessment / diagnostic-suggestion software *can* be a
   regulated medical device. In Malaysia this falls under the **Medical Device Act 2012** (Medical
   Device Authority); in the EU under **MDR 2017/745** (cf. DxGPT's own Class IIa classification under
   Rule 11). Positioning as "educational" reduces but does not guarantee exemption — get a regulatory
   determination before commercial launch.
2. **Professional legal review** of the ToS and Privacy Policy (currently self-drafted). — see §6.
3. **Age-eligibility enforcement.** ToS §4 requires users to be 18+ (or guardian-supervised), but
   registration collects age without enforcing a minimum. Add a check at registration if the
   18+ requirement is to be real.
4. **Versioned consent record.** Store *which version* of the ToS/Privacy a user accepted and *when*,
   so consent is auditable if challenged (ties to the §3 column-rename note).

## 5. Report-storage consent

Saving a diagnostic report stores health data, so it requires its own explicit step:

- "Save to my account" appears only for logged-in users on the final report and opens a confirmation
  dialog explaining that symptom text + AI analysis + recommendations are stored as health data,
  that the chat assistant will use saved reports, and that deletion is permanent
  ([`FinalReportPage.tsx`](../my-app/src/pages/diagnosis/FinalReportPage.tsx)).
- **Backend alignment:** report ingestion into the chat assistant's store was moved from the automatic
  report endpoint to the explicit save endpoint
  ([`auth_routes.py`](../backend/api/auth_routes.py) `save-medical-report`), so nothing persists
  unless the user confirms. This matches the chatbot's "answers from your saved reports only" claim.

## 6. Recommended next steps before production

1. Engage a lawyer (Malaysian + any target market) to review the ToS and Privacy Policy.
2. Obtain a regulatory determination under the Medical Device Act 2012 (and MDR if targeting the EU).
3. Enforce 18+ at registration (or implement guardian consent).
4. Migrate the consent flag to a versioned, timestamped record.
5. Keep an internal incident/breach-notification process (PDPA / GDPR Art. 33 require timely notice).

---

### Does a privacy policy prevent being sued?

No. A privacy policy is a transparency document; **breaking** it is grounds for action, and on its
own it does not limit liability. The combination that reduces real lawsuit risk is: a **Terms of
Service** (liability limitation + assumption of risk), **honest** legal documents you actually
follow, **consistent educational/non-device positioning**, and resolving the **regulatory** question
for your jurisdiction. Items 1–3, 5 are implemented in the app; items 4 (regulatory + legal review),
6, 7 remain and are largely outside the codebase.
