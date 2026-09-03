import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from '@/components/ui/accordion';
import { Info, ListChecks, RotateCcw, HelpCircle, FileCheck } from 'lucide-react';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { CandidateCard } from 'components/medical/CandidateCard';
import { DiagnosisView } from 'types/diagnosis';

interface Props {
  view: DiagnosisView;
  loading: boolean;
  onAnswerQuestions: () => void;
  onFinalize: () => void;
  onReset: () => void;
}

const EXPANDED = 3;

export const EvidenceResultsPage: React.FC<Props> = ({
  view, loading, onAnswerQuestions, onFinalize, onReset,
}) => {
  const flat = view.ranking.flatMap(group =>
    group.diagnoses.map(name => ({
      name, rank: group.rank, tied: group.diagnoses.length > 1,
    }))
  );
  // Expand whole tie groups. Slicing the flattened list would show one
  // member of a tie while hiding its ties, which defeats the point of
  // surfacing the tie at all.
  let cut = 0;
  for (const group of view.ranking) {
    if (cut >= EXPANDED) break;
    cut += group.diagnoses.length;
  }
  const shown = flat.slice(0, cut);
  const rest = flat.slice(cut);
  const hasTies = view.ranking.some(g => g.diagnoses.length > 1);

  return (
    <div className="space-y-6 animate-fade-in-up">
      <DiagnosisProgress current="evidence" />

      {hasTies && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Some conditions are equally supported by what you have told us so far.
            Answering a few more questions can separate them.
          </AlertDescription>
        </Alert>
      )}

      <p className="text-xs text-muted-foreground leading-relaxed px-1">
        <span className="font-medium text-foreground">Strong</span>,{' '}
        <span className="font-medium text-foreground">moderate</span> and{' '}
        <span className="font-medium text-foreground">weak</span> show how central
        each detail/symptom is to that condition.
      </p>

      <div className="space-y-4">
        {shown.map(c => (
          <CandidateCard
            key={c.name}
            diagnosis={c.name}
            rank={c.rank}
            tied={c.tied}
            criteria={view.matrix[c.name] ?? {}}
            canonical={view.canonical}
            judgements={view.judgements}
            explanation={view.explanations[c.name] ?? null}
          />
        ))}
      </div>

      {rest.length > 0 && (
        <Accordion type="single" collapsible>
          <AccordionItem value="more">
            <AccordionTrigger className="text-sm">
              {rest.length} more condition{rest.length > 1 ? 's' : ''} considered
            </AccordionTrigger>
            <AccordionContent className="space-y-4 pt-2">
              {rest.map(c => (
                <CandidateCard
                  key={c.name}
                  diagnosis={c.name}
                  rank={c.rank}
                  tied={c.tied}
                  criteria={view.matrix[c.name] ?? {}}
                  canonical={view.canonical}
                  judgements={view.judgements}
                  explanation={view.explanations[c.name] ?? null}
                />
              ))}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}

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

      {/* Finalising is always available. It is the only route to the report, and
          the report is the only copy the user gets — gating it on open_questions
          stranded anyone whose differential produced none. */}
      <div className="flex gap-3 flex-wrap">
        <Button onClick={onFinalize} disabled={loading} className="gap-2">
          <FileCheck className="h-4 w-4" />
          Finish and get report
        </Button>
        {view.open_questions.length > 0 && (
          <Button variant="secondary" onClick={onAnswerQuestions} disabled={loading} className="gap-2">
            <ListChecks className="h-4 w-4" />
            Answer {view.open_questions.length} question
            {view.open_questions.length > 1 ? 's' : ''}
          </Button>
        )}
        <Button variant="ghost" onClick={onReset} disabled={loading} className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Start over
        </Button>
      </div>
    </div>
  );
};
