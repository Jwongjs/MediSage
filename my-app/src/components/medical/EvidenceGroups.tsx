import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Check, X, HelpCircle } from 'lucide-react';
import { Criterion, Judgement, Importance, EvidenceStatus } from 'types/diagnosis';

const GROUPS: { status: EvidenceStatus; label: string; cls: string; Icon: typeof Check }[] = [
  { status: 'supported',     label: 'Supported',   cls: 'evidence-supported',    Icon: Check },
  { status: 'contradicted',  label: 'Contradicted', cls: 'evidence-contradicted', Icon: X },
  { status: 'not_mentioned', label: 'Unaddressed', cls: 'evidence-unaddressed',  Icon: HelpCircle },
];

const IMPORTANCE_ORDER: Record<Importance, number> = { strong: 0, moderate: 1, weak: 2 };

interface Props {
  criteria: Record<string, Importance>;
  canonical: Criterion[];
  judgements: Record<string, Judgement>;
}

export const EvidenceGroups: React.FC<Props> = ({ criteria, canonical, judgements }) => {
  const byKey = new Map(canonical.map(c => [c.key, c]));

  const rows = Object.entries(criteria)
    .map(([key, importance]) => ({
      key,
      importance,
      label: byKey.get(key)?.plain_label || byKey.get(key)?.label || key,
      judgement: judgements[key] ?? { status: 'not_mentioned' as const, evidence: null, source: 'llm' as const },
    }))
    .sort((a, b) => IMPORTANCE_ORDER[a.importance] - IMPORTANCE_ORDER[b.importance]);

  return (
    <div className="space-y-4">
      {GROUPS.map(({ status, label, cls, Icon }) => {
        const group = rows.filter(r => r.judgement.status === status);
        if (group.length === 0) return null;

        return (
          <div key={status}>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5" />
              {label}
              <span className="font-normal normal-case tracking-normal">({group.length})</span>
            </p>
            <ul className="space-y-1.5">
              {group.map(row => (
                <li key={row.key} className={cn('rounded-lg border px-3 py-2', cls)}>
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm leading-snug">{row.label}</span>
                    <Badge variant="outline" className="text-[10px] shrink-0 capitalize">
                      {row.importance}
                    </Badge>
                  </div>
                  {row.judgement.evidence && (
                    <p className="text-xs mt-1.5 italic opacity-80 whitespace-pre-line">
                      “{row.judgement.evidence}”
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
};
