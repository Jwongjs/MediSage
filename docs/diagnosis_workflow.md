Clean New Workflow (No Patching Old Logic)
Remove conditional routing entirely. Linear pipeline with guided data collection stages:


POST /diagnosis/start  { symptoms, patient_intake }
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │              llm_diagnosis                   │
    │                                              │
    │  • Injection sanitization + Prompt Guard     │
    │  • detect_critical_symptoms()                │
    │  • Single LLM call → returns BOTH:           │
    │      - top 5 differential (with layman term) │
    │      - sign_prompts[] to check               │
    │  • workflow_path = ["initial_assessment"]    │
    └─────────────────────────────────────────────┘
          │  (no routing — always linear)
⏸ interrupt_before process_signs
          │
  POST /resume  { sign_responses: {...} }
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │           process_signs  (thin, no LLM)      │
    │  • Records sign_responses → userInput_signs  │
    │  • workflow_path.append("signs_collected")   │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │       generate_followup_questions            │
    │                                              │
    │  • LLM: 4 adaptive questions using           │
    │    intake + symptoms + signs + differential  │
    └─────────────────────────────────────────────┘
          │  (no interrupt — runs automatically
          │   after process_signs in same resume)
⏸ interrupt_before process_followup_responses
          │
  POST /resume  { answers: {...} }
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │       process_followup_responses             │
    │                                              │
    │  • LLM re-runs differential with full        │
    │    context: intake + symptoms + signs + QnA  │
    │  • Computes average_confidence (report only) │
    │  • workflow_path.append("followup_complete") │
    └─────────────────────────────────────────────┘
          │
⏸ interrupt_before overall_analysis
          │
  POST /resume (no body)
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │           overall_analysis                   │
    │  • intake context prepended                  │
    │  • routes on workflow_path value             │
    │  • critical severity floor if flagged        │
    └─────────────────────────────────────────────┘
          │
⏸ interrupt_before medical_report
          │
  POST /resume (no body)
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │            medical_report                    │
    │  • Patient info section                      │
    │  • Emergency banner if critical              │
    │  • Confidence level displayed (not gating)   │
    │  • Layman terms, alternative diagnoses       │
    └─────────────────────────────────────────────┘
          │
         END
What this removes from the codebase entirely:

_route_after_diagnosis and _route_after_followup conditional functions
requires_skin_cancer_screening, requires_user_input, average_confidence as routing gates
The follow-up loop (requires_user_input flag that re-routes to generate_followup_questions)
All ABCDE / skin cancer paths
FollowUpInteractionNode.handle_followup_interaction dispatch logic (replaced by two dedicated nodes)

Overall Audit Verdict
Dimension	Current Plan	Verdict
Performance	5 nodes, ~6 LLM calls	Acceptable. Sign prompts embedded in diagnosis call keeps it at ~6. No extra.
Cost	~$0.02-0.03/session	Fine. Linear flow with no loops means predictable cost ceiling.
Security	No input sanitization, PHI in logs	Fix needed. Injection sanitization + remove print(user_input) + wrap user content in XML tags.
Medical-legal	"diagnosis" terminology, no disclaimer in output, confidence shown as number	High risk. Change "diagnosis" → "preliminary differential assessment" throughout. Don't show raw confidence percentage to patients — show qualitative: High / Moderate / Low certainty. Add prominent disclaimer to medical report.
One medical-legal flag worth calling out: the current average_confidence is computed by averaging LLM-assigned confidence scores from a parse_diagnosis_details list. Displaying this number to patients as if it's validated clinical accuracy invites liability. Replacing it with a qualitative label ("Initial assessment — further evaluation recommended") is safer and more honest.