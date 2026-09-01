import { DiagnosisView, HistoryEntry, Answer } from 'types/diagnosis';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export class DiagnosisService {
  static async start(patientText: string, sessionId?: string) {
    const body = new FormData();
    body.append('patient_text', patientText);
    if (sessionId) body.append('session_id', sessionId);
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/start`, {
        method: 'POST', body, credentials: 'include',
      })
    );
  }

  static async submitAnswers(sessionId: string, answers: Record<string, Answer>) {
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/${sessionId}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers),
        credentials: 'include',
      })
    );
  }

  static async finalize(sessionId: string) {
    return handle<{ session_id: string; result: DiagnosisView }>(
      await fetch(`${API_BASE_URL}/diagnosis/${sessionId}/finalize`, {
        method: 'POST', credentials: 'include',
      })
    );
  }

  static async history() {
    return handle<{ sessions: HistoryEntry[] }>(
      await fetch(`${API_BASE_URL}/diagnosis/history`, { credentials: 'include' })
    );
  }

  static async historyDetail(rowId: string) {
    return handle<Record<string, unknown>>(
      await fetch(`${API_BASE_URL}/diagnosis/history/${rowId}`, { credentials: 'include' })
    );
  }

  static async deleteHistory(rowId: string) {
    return handle<{ deleted: string }>(
      await fetch(`${API_BASE_URL}/diagnosis/history/${rowId}`, {
        method: 'DELETE', credentials: 'include',
      })
    );
  }
}
