# Diagnosis Workflow → RAG Chatbot: Boundary Scenario

**Purpose:** Reference scenario showing the information boundary between the Diagnosis Workflow and the RAG Chatbot, confirming there is no output overlap between the two features.

---

## Scenario: Sarah, 32F — Lower Back Pain

---

## Stage 1 — Diagnosis Workflow

> **What it does:** Active reasoning from current input. The LLM generates a new assessment.

**Step 1 — Symptoms submitted**
> "Lower back pain for 2 weeks, sharp shooting pain down my left leg, gets worse when I sit for long periods."

**Step 2 — Sign prompts** *(LLM generates based on symptoms)*
> Before we continue, please check the following:
> - Do you feel any numbness or tingling in your left leg or foot?
> - Does bending forward make the pain worse?
> - Any noticeable leg weakness when walking?

**Step 3 — Sarah's signs**
> "Yes, tingling in my left foot. Bending forward definitely makes it worse. No weakness."

**Step 4 — Adaptive follow-up questions** *(generated using symptoms + signs + differential)*
> 1. Does the pain wake you at night?
> 2. Any bowel or bladder changes?
> 3. On a scale of 1–10, how severe is the pain right now?
> 4. Any recent injury, or did this start without a clear trigger?

**Step 5 — Sarah's answers**
> "No night waking. No bowel changes. Pain is 7/10. No injury, just started one morning."

**Step 6 — Medical Report generated**

```
PRELIMINARY DIFFERENTIAL ASSESSMENT
────────────────────────────────────
PATIENT: Sarah, 32F
Medications: None | Allergies: None

PRIMARY ASSESSMENT
Lumbar Disc Herniation (slipped disc) — High Certainty

What this means: A lumbar disc herniation occurs when the soft
inner cushion of a spinal disc pushes outward and presses on a
nearby nerve. The most common cause is wear and tear or sustained
pressure. This explains the shooting pain down your leg.

Clinical Reasoning: Unilateral radiculopathy with L5/S1
dermatomal distribution. Flexion-aggravated, paresthesia in foot,
absent red flags (no night pain, no bowel/bladder changes).

Severity: Moderate
Specialist: Orthopedic surgeon or neurologist

ALTERNATIVE ASSESSMENTS
- Lumbar spinal stenosis — Low Certainty
- Piriformis syndrome — Low Certainty

⚠ This is a preliminary differential assessment, not a diagnosis.
  Please consult a qualified healthcare professional.
```

> The report is auto-ingested into pgvector via BackgroundTasks after generation.

---

## Stage 2 — RAG Chatbot (after viewing report)

> **What it does:** Retrieval from stored documents. The LLM synthesizes what is already written — it does not reason from new symptoms.

---

**Q1: "What exactly is a lumbar disc herniation?"**

Chatbot retrieves the *What this means* chunk from the ingested report.

> "From your assessment today: A lumbar disc herniation occurs when the soft inner cushion of a spinal disc pushes outward and presses on a nearby nerve. The most common cause is wear and tear or sustained pressure."

*Retrieves the user explanation already written by the diagnosis workflow. Does not generate a new definition.*

---

**Q2: "Should I be worried? Is this serious?"**

Chatbot retrieves severity and specialist fields from the report.

> "Your assessment noted moderate severity and recommended consulting an orthopedic surgeon or neurologist. This is not flagged as an emergency, but a professional appointment is advised. I can only tell you what your assessment recorded — please consult your doctor for a personal opinion."

*Does not make a new severity judgment.*

---

**Q3: "I also developed a slight fever this morning — could it be related?"**

New symptom not present in the diagnosis session.

> "I can only answer questions about your existing medical records. Fever was not part of your assessment. For new symptoms, please start a new assessment using the diagnosis feature so it can be properly evaluated."

*Hard boundary — no new symptoms accepted, redirects to the diagnosis workflow.*

---

**Q4: "What's the difference between an orthopedic surgeon and a neurologist for this?"**

Chatbot retrieves the specialist recommendation context.

> "Your assessment recommended either an orthopedic surgeon or a neurologist. Orthopedic surgeons specialize in the musculoskeletal system including the spine, while neurologists focus on nerve-related conditions. Both can evaluate disc herniations — your GP can advise which is more appropriate for your specific case."

*Grounded in report context. Does not speculate beyond what the report stated.*

---

**Q5 (3 months later): "Can I see what my assessment was back in March?"**

> "From your assessment on March 10, 2026:
> Primary: Lumbar Disc Herniation — High Certainty
> Severity: Moderate. Specialist: Orthopedic surgeon or neurologist.
> [full report context retrieved]"

*Strongest chatbot use case — historical retrieval across sessions. The diagnosis workflow has no cross-session memory; the chatbot has all of it.*

---

## The Boundary

```
DIAGNOSIS WORKFLOW                    RAG CHATBOT
─────────────────────────────────     ─────────────────────────────────
Active session only                   Historical + current stored reports
LLM generates new assessment          LLM retrieves and summarizes only
Input: symptoms, signs, Q&A           Input: natural language question
Output: new differential assessment   Output: what documents contain
Handles: new symptoms                 Cannot handle: new symptoms
Scope: one session at a time          Scope: spans all past sessions
```

---

## Overlap Cases and How They Are Handled

| User question | Incorrect behavior | Correct behavior |
|---|---|---|
| "Could this be cancer?" | Chatbot speculates | "I cannot make new assessments. Please start a new diagnosis session." |
| "My pain is worse today" | Chatbot extends last diagnosis | "For changes in symptoms, please start a new assessment." |
| "What did the report say about severity?" | Diagnosis workflow retrieves history | Chatbot only — diagnosis workflow reads current `AgentState`, not past sessions |
| "Based on my reports, am I at risk of X?" | Either system speculates | Chatbot retrieves relevant historical context, adds disclaimer, does not speculate |

---

## Why There Is No Output Overlap

1. **The diagnosis workflow only reads `AgentState` for the current `thread_id`** — it has no access to past sessions and cannot retrieve previous reports.
2. **The RAG chatbot never generates a new differential from user-described symptoms** — enforced by boundary rules in `_synthesize_node`.
3. **Each system redirects the other's use case** rather than attempting to handle it.
4. **The medical report is the handoff artifact** — the diagnosis workflow produces it, the chatbot retrieves it. Neither system duplicates the other's output.
