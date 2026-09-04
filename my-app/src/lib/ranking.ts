import type { EvidenceStatus, Importance, Judgement } from 'types/diagnosis';

const IMPORTANCES: Importance[] = ['strong', 'moderate', 'weak'];
const STATUSES: EvidenceStatus[] = ['supported', 'contradicted', 'not_mentioned'];

/** Checkbox state is the only thing that can override an llm-sourced
 * judgement's status for display purposes; contradicted can never be
 * reached this way since it's never rendered as a checkbox. */
export function effectiveStatus(
  judgement: Judgement | undefined,
  checked: boolean,
): EvidenceStatus {
  if (judgement?.status === 'contradicted') return 'contradicted';
  return checked ? 'supported' : 'not_mentioned';
}

function tally(
  diagnosis: string,
  matrix: Record<string, Record<string, Importance>>,
  statuses: Record<string, EvidenceStatus>,
): Map<string, number> {
  const counts = new Map<string, number>();
  for (const [key, importance] of Object.entries(matrix[diagnosis] ?? {})) {
    let status = statuses[key] ?? 'not_mentioned';
    if (!STATUSES.includes(status)) status = 'not_mentioned';
    const k = `${importance}:${status}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return counts;
}

function sortKey(counts: Map<string, number>): number[] {
  const g = (i: Importance, s: EvidenceStatus) => counts.get(`${i}:${s}`) ?? 0;
  return [
    g('strong', 'contradicted'),
    -g('strong', 'supported'),
    g('strong', 'not_mentioned'),
    g('moderate', 'contradicted'),
    -g('moderate', 'supported'),
    g('moderate', 'not_mentioned'),
    g('weak', 'contradicted'),
    -g('weak', 'supported'),
  ];
}

function compareKeys(a: number[], b: number[]): number {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

/** Diagnoses grouped into tiers. Diagnoses in one tier are genuinely tied.
 * Faithful port of ranking.py's tally/sort_key/rank -- same tuple, same
 * lexicographic ordering, same "neutral, not last" semantics for an empty
 * tally. Kept in sync by hand; there is no shared source of truth between
 * the Python and TypeScript copies. */
export function rank(
  matrix: Record<string, Record<string, Importance>>,
  statuses: Record<string, EvidenceStatus>,
): string[][] {
  const diagnoses = Object.keys(matrix);
  const scored = diagnoses
    .map(d => ({ key: sortKey(tally(d, matrix, statuses)), name: d }))
    .sort((a, b) => compareKeys(a.key, b.key) || a.name.localeCompare(b.name));

  const groups: string[][] = [];
  for (const { key, name } of scored) {
    const last = groups[groups.length - 1];
    const lastKey = last ? sortKey(tally(last[0], matrix, statuses)) : null;
    if (last && lastKey && compareKeys(lastKey, key) === 0) {
      last.push(name);
      last.sort();
    } else {
      groups.push([name]);
    }
  }
  return groups;
}
