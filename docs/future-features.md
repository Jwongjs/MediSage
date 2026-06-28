# MediSage — Future Features

Features deferred from current sprint scope. Each entry notes what it requires and why it was deferred.

---

## Privacy & Compliance

### PHI-Safe Document Upload for RAG Chatbot
**What:** Allow users to upload external medical documents (lab results, doctor's notes, prescriptions, hospital discharge summaries). Strip structured PHI (SSN, MRN, DOB, phone, email) via regex redaction before chunking and embedding. Store only de-identified chunks — discard the original file. Give users a delete endpoint to wipe their data.

**Why this matters:** Transforms the chatbot from "re-read your MediSage report" to "query your entire medical history in plain English." Patients receive dense clinical documents they don't understand — this solves a real problem.

**Why deferred:** PHI redaction needs careful testing to avoid stripping medical values (e.g. date ranges in lab results vs. patient DOB). Requires a consent notice UI and a document delete endpoint. Needs its own QA pass before touching real health data.

**Requires:**
- `backend/rag/phi_redactor.py` — regex patterns for SSN, MRN, DOB labels, phone, email
- Upload endpoint: `POST /documents/upload` — accepts PDF/text, redacts, chunks, embeds, discards original
- Delete endpoint: `DELETE /documents/{source_id}` — removes all pgvector chunks for that source
- Frontend upload UI with consent notice
- Consider spaCy NER for name redaction (optional, adds dependency)

**Note:** Not HIPAA compliant at this stage (no BAA with Anthropic/Supabase). Structured PHI redaction is a meaningful mitigation but does not constitute full compliance.

---

### Full HIPAA Compliance
**What:** Business Associate Agreement (BAA) with Anthropic and Supabase, audit trail for all PHI access, data residency controls, formal risk assessment.

**Why deferred:** Enterprise-level requirement. Out of scope for a portfolio project. Relevant only if MediSage moves toward real clinical deployment.

---

## Clinical Extensions

### Skin Lesion Image Analysis
**What:** Accept a photo of a skin lesion and run it through a dermatology classification model (e.g. EfficientNet trained on ISIC dataset). Was originally part of SP1 but removed because it required a separate ML model that wasn't available.

**Why deferred:** Requires a trained, validated classification model. Cannot be replaced by a general-purpose LLM for image diagnosis — medical image classification needs a purpose-built model with proper validation. High regulatory risk if mislabeled.

**Requires:** Trained dermatology model, image preprocessing pipeline, model serving infrastructure, clinical validation.

---

### Medication Interaction Checking
**What:** After the overall analysis, cross-reference the patient's current medications (from intake) against the preliminary diagnosis and any likely new prescriptions. Flag known interactions.

**Why deferred:** Requires a drug interaction database (e.g. DrugBank, OpenFDA). The LLM alone is not reliable enough for this — drug interactions require a structured, verified data source.

---

### Second Opinion Flow
**What:** Allow a user to optionally submit their MediSage assessment to a licensed human clinician for review. The clinician receives the de-identified report and provides a written response.

**Why deferred:** Requires clinician network/partnerships, payment processing, async response handling, and legal framework.

---

## User Experience

### Symptom & Condition History Tracking
**What:** A timeline view showing all past assessments — what was assessed, severity, specialist recommended, and whether the user followed up. Highlights recurring conditions.

**Why deferred:** Needs a dedicated history UI and aggregation query across past `thread_id` sessions. Currently, past sessions are accessible via the RAG chatbot but not surfaced in a structured timeline view.

---

### PDF Report Export
**What:** Allow users to download their medical report as a formatted PDF to share with their doctor.

**Why deferred:** Minor feature, easy to implement with a library like `weasyprint` or `reportlab`. Deferred to keep SP3 focused.

---

### Emergency Contact Notification
**What:** If `critical_symptoms_detected = True`, optionally notify a pre-configured emergency contact via SMS or email alongside showing the emergency banner.

**Why deferred:** Requires Twilio/SendGrid integration and user-configured contact management. High value but adds external service dependencies.

---

## Platform & Infrastructure

### Wearable / Health App Integration
**What:** Pull data from Apple Health, Google Fit, or Fitbit (resting heart rate, blood pressure, SpO2, sleep data) and include it as context in the diagnosis intake. Gives the LLM objective biometric data alongside subjective symptoms.

**Why deferred:** Requires OAuth flows with each health platform. Data normalization across sources is non-trivial.

---

### Family / Dependent Management
**What:** Allow a user to manage health records for dependents (children, elderly parents). Each dependent has a separate `user_id` scoped profile with their own diagnosis history and uploaded documents.

**Why deferred:** Requires account hierarchy (parent/child relationship), consent management, and multi-profile UI. Meaningful scope increase.

---

### Clinician-Facing Dashboard
**What:** A separate portal for healthcare providers to review patient-submitted assessments before appointments. Patients share a read-only link to their report.

**Why deferred:** Requires separate auth role, sharing/permission model, and is a B2B feature that changes the product positioning significantly.

---

### Multi-Language Support
**What:** Localize the diagnosis prompts, report output, and UI for non-English speakers. The LLM already supports multilingual output — the main work is detecting input language and routing prompts accordingly.

**Why deferred:** Testing medical accuracy across languages requires native-speaker clinical review. Not just a translation problem.
