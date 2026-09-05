import React from 'react';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

export type DiagnosisStage = 'symptoms' | 'analysis' | 'followup' | 'report';

const STAGES: { id: DiagnosisStage; label: string }[] = [
  { id: 'symptoms', label: 'Symptoms'  },
  { id: 'analysis', label: 'Analysis'  },
  { id: 'followup', label: 'Follow-up' },
  { id: 'report',   label: 'Report'    },
];

interface DiagnosisProgressProps {
  current: DiagnosisStage;
}

export const DiagnosisProgress: React.FC<DiagnosisProgressProps> = ({ current }) => {
  const ci = STAGES.findIndex(s => s.id === current);

  return (
    <nav aria-label="Diagnosis progress">
      <ol className="flex items-center">
        {STAGES.map(({ id, label }, i) => {
          const done   = i < ci;
          const active = i === ci;
          return (
            <li key={id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1">
                <div className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-all',
                  done   && 'bg-accent text-accent-foreground',
                  active && 'bg-primary text-primary-foreground ring-4 ring-primary/20',
                  !done && !active && 'bg-secondary text-muted-foreground',
                )}>
                  {done ? <Check className="h-3.5 w-3.5" /> : <span>{i + 1}</span>}
                </div>
                <span className={cn(
                  'text-[10px] sm:text-xs font-medium hidden sm:block',
                  active ? 'text-primary' : done ? 'text-accent' : 'text-muted-foreground',
                )}>
                  {label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div className={cn('h-px flex-1 -mt-4 mx-1 transition-colors', i < ci ? 'bg-accent' : 'bg-border')} />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
