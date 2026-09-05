import React, { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, RotateCcw, HelpCircle, FileCheck } from 'lucide-react';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { CandidateCard } from 'components/medical/CandidateCard';
import { DiagnosisView } from 'types/diagnosis';
import { rank, effectiveStatus } from 'lib/ranking';

interface Props {
  view: DiagnosisView;
  loading: boolean;
  onFinalize: (checked: string[]) => void;
  onReset: () => void;
}

export const EvidenceResultsPage: React.FC<Props> = ({
  view, loading, onFinalize, onReset,
}) => {
  // Local overrides only: a key here means the user has explicitly
  // toggled it away from whatever judgements[key].status originally said.
  // Never holds a contradicted key -- there is no checkbox for one.
  const [checked, setChecked] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    for (const c of view.canonical) {
      if (view.judgements[c.key]?.status === 'supported') initial.add(c.key);
    }
    return initial;
  });

  const toggle = (key: string) => {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const liveRanking = useMemo(() => {
    const statuses: Record<string, ReturnType<typeof effectiveStatus>> = {};
    for (const c of view.canonical) {
      statuses[c.key] = effectiveStatus(view.judgements[c.key], checked.has(c.key));
    }
    const matrix = Object.fromEntries(
      Object.keys(view.matrix).filter(d => !view.not_evaluated.includes(d)).map(d => [d, view.matrix[d]])
    );
    return rank(matrix, statuses);
  }, [view.canonical, view.judgements, view.matrix, view.not_evaluated, checked]);

  const flat = liveRanking.flatMap((group, i) =>
    group.map(name => ({ name, rank: i + 1, tied: group.length > 1 }))
  );
  const hasTies = liveRanking.some(g => g.length > 1);

  return (
    <div className="space-y-6 animate-fade-in-up">
      <DiagnosisProgress current="evidence" />

      {hasTies && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Some conditions are equally supported by what you have checked so far.
            Checking a few more symptoms can separate them.
          </AlertDescription>
        </Alert>
      )}

      <p className="text-xs text-muted-foreground leading-relaxed px-1">
        <span className="font-medium text-foreground">Strong</span>,{' '}
        <span className="font-medium text-foreground">moderate</span> and{' '}
        <span className="font-medium text-foreground">weak</span> show how central
        each detail/symptom is to that condition. Check the ones that apply to you —
        the ranking updates as you go.
      </p>

      <div className="space-y-4">
        {flat.map(c => (
          <CandidateCard
            key={c.name}
            diagnosis={c.name}
            rank={c.rank}
            tied={c.tied}
            criteria={view.matrix[c.name] ?? {}}
            canonical={view.canonical}
            judgements={view.judgements}
            checked={checked}
            onToggle={toggle}
            explanation={view.explanations[c.name] ?? null}
          />
        ))}
      </div>

      {view.not_evaluated.length > 0 && (
        <div className="bg-secondary/60 rounded-lg p-4">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
            <HelpCircle className="h-3.5 w-3.5" />
            Considered, not assessed
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed mb-2.5">
            These conditions came up but could not be evaluated against what you have told us,
            there was not enough to build a criteria profile for them. That is different from
            ranking last: they were not scored at all, so their absence above is not a judgement
            against them.
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {view.not_evaluated.map(name => (
              <li key={name}>
                <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
                  {name}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-3 flex-wrap">
        <Button onClick={() => onFinalize(Array.from(checked))} disabled={loading} className="gap-2">
          <FileCheck className="h-4 w-4" />
          Finish and get report
        </Button>
        <Button variant="ghost" onClick={onReset} disabled={loading} className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Start over
        </Button>
      </div>
    </div>
  );
};
