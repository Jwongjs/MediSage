import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { Check, X } from 'lucide-react';
import { Criterion, Judgement, Importance } from 'types/diagnosis';
import { effectiveStatus } from 'lib/ranking';

const IMPORTANCE_ORDER: Record<Importance, number> = { strong: 0, moderate: 1, weak: 2 };

interface Props {
  criteria: Record<string, Importance>;
  canonical: Criterion[];
  judgements: Record<string, Judgement>;
  checked: Set<string>;
  onToggle: (key: string) => void;
}

export const EvidenceGroups: React.FC<Props> = ({ criteria, canonical, judgements, checked, onToggle }) => {
  const byKey = new Map(canonical.map(c => [c.key, c]));

  const rows = Object.entries(criteria)
    .map(([key, importance]) => ({
      key,
      importance,
      label: byKey.get(key)?.plain_label || byKey.get(key)?.label || key,
      status: effectiveStatus(judgements[key], checked.has(key)),
    }))
    .sort((a, b) => IMPORTANCE_ORDER[a.importance] - IMPORTANCE_ORDER[b.importance]);

  const contradicted = rows.filter(r => r.status === 'contradicted');
  const interactive = rows.filter(r => r.status !== 'contradicted');

  return (
    <div className="space-y-4">
      {contradicted.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <X className="h-3.5 w-3.5" />
            Contradicted
            <span className="font-normal normal-case tracking-normal">({contradicted.length})</span>
          </p>
          <ul className="space-y-1.5">
            {contradicted.map(row => (
              <li key={row.key} className="rounded-lg border px-3 py-2 evidence-contradicted">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm leading-snug">{row.label}</span>
                  <Badge variant="outline" className="text-[10px] shrink-0 capitalize">
                    {row.importance}
                  </Badge>
                </div>
                {judgements[row.key]?.evidence && (
                  <p className="text-xs mt-1.5 italic opacity-80 whitespace-pre-line">
                    "{judgements[row.key].evidence}"
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {interactive.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5" />
            Do you have these?
          </p>
          <ul className="space-y-1.5">
            {interactive.map(row => (
              <li key={row.key} className={cn('rounded-lg border px-3 py-2 flex items-start gap-2.5', row.status === 'supported' && 'evidence-supported')}>
                <Checkbox
                  id={`sym-${row.key}`}
                  checked={row.status === 'supported'}
                  onCheckedChange={() => onToggle(row.key)}
                  className="mt-0.5"
                />
                <label htmlFor={`sym-${row.key}`} className="flex-1 flex items-start justify-between gap-2 cursor-pointer">
                  <span className="text-sm leading-snug">{row.label}</span>
                  <Badge variant="outline" className="text-[10px] shrink-0 capitalize">
                    {row.importance}
                  </Badge>
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
