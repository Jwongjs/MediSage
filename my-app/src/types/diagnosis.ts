// Mirrors backend/schemas/diagnosis_schemas.py.
// There is no confidence field anywhere in this system by design.

export type Importance = 'strong' | 'moderate' | 'weak';
export type EvidenceStatus = 'supported' | 'contradicted' | 'not_mentioned';
export type CriterionKind = 'symptom' | 'history' | 'lab' | 'imaging' | 'demographic';
export type Answer = 'yes' | 'no' | 'unsure';

export interface Criterion {
  key: string;
  label: string;
  kind: CriterionKind;
}

export interface Judgement {
  status: EvidenceStatus;
  evidence: string | null;
  source: 'llm' | 'patient_answer';
}

export interface RankGroup {
  rank: number;
  diagnoses: string[];
}

export interface Summary {
  severity: string;
  specialist_recommendation: string;
  user_explanation?: string | null;
  explanation_source?: string | null;
  explanation_url?: string | null;
}

export interface DiagnosisView {
  stage: string;
  patient_text: string;
  ranking: RankGroup[];
  /** Candidates whose criteria profile could not be built. NOT ranked —
   *  an empty tally would sort them above honestly-evaluated candidates. */
  not_evaluated: string[];
  canonical: Criterion[];
  matrix: Record<string, Record<string, Importance>>;
  judgements: Record<string, Judgement>;
  open_questions: string[];
  grounded: Record<string, boolean>;
  summary: Summary | null;
}

export interface HistoryEntry {
  id: string;
  session_id: string;
  title: string;
  created_at: string;
}
