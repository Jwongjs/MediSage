import { DiagnosisView, Answer, ExportFormat } from 'types/diagnosis';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Session state lives in memory only, so a restart makes every id unknown.
// That 404 is the likeliest error a real user meets; it must read as English,
// not as the FastAPI envelope it arrives in.
const SESSION_GONE = 'This session has expired. Please start a new assessment.';

async function assertOk(res: Response): Promise<Response> {
  if (!res.ok) {
    if (res.status === 404) throw new Error(SESSION_GONE);
    const body = await res.text();
    let detail = body;
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed?.detail === 'string') detail = parsed.detail;
    } catch {
      // Not JSON — the raw body is the best message available.
    }
    throw new Error(detail || `Request failed with ${res.status}`);
  }
  return res;
}

async function handle<T>(res: Response): Promise<T> {
  return (await assertOk(res)).json() as Promise<T>;
}

const EXPORT_EXTENSION: Record<ExportFormat, string> = { pdf: 'pdf', word: 'docx' };

export class DiagnosisService {
  static async start(patientText: string) {
    const body = new FormData();
    body.append('patient_text', patientText);
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/start`, { method: 'POST', body })
    );
  }

  static async submitAnswers(sessionId: string, answers: Record<string, Answer>) {
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/${sessionId}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers),
      })
    );
  }

  static async finalize(sessionId: string) {
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/${sessionId}/finalize`, { method: 'POST' })
    );
  }

  /** Streams the generated report and hands it straight to the browser.
   *  Nothing is stored server-side, so this file is the user's only copy. */
  static async exportReport(
    sessionId: string,
    format: ExportFormat,
    includeDetails: boolean = true,
  ): Promise<void> {
    const body = new FormData();
    body.append('session_id', sessionId);
    body.append('format', format);
    body.append('include_details', String(includeDetails));

    const res = await assertOk(
      await fetch(`${API_BASE_URL}/patient/export_report`, { method: 'POST', body })
    );

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `medisage-differential-${new Date().toISOString().slice(0, 10)}.${EXPORT_EXTENSION[format]}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }
}
