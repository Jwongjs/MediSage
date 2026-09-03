import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Loader2, ListChecks } from 'lucide-react';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { DiagnosisView, Answer } from 'types/diagnosis';

interface Props {
  view: DiagnosisView;
  loading: boolean;
  onSubmit: (answers: Record<string, Answer>) => Promise<void>;
  onSkip: () => void;
}

const OPTIONS: { value: Answer; label: string }[] = [
  { value: 'yes',    label: 'Yes' },
  { value: 'no',     label: 'No' },
  { value: 'unsure', label: 'Not sure' },
];

const MAX_QUESTIONS = 8;

// A criterion label is sometimes itself a negation (e.g. "No nausea or
// vomiting" -- a real diagnostic criterion, not a typo). Wrapping that in
// "Do you have {label}?" produces a double negative ("Do you have no nausea
// or vomiting?") that's confusing to answer. Answering "Yes" still means the
// criterion holds, exactly as for a positive label -- only the wording
// changes, not the yes/no mapping.
function questionFor(label: string): string {
  const negated = label.match(/^no\s+(.+)$/i);
  return negated ? `Are you free of ${negated[1]}?` : `Do you have ${label}?`;
}

export const CriterionPickerPage: React.FC<Props> = ({ view, loading, onSubmit, onSkip }) => {
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  // Local in-flight latch. The server reads the session, recomputes, then
  // writes back with no compare-and-set, so two overlapping submissions
  // silently discard one of them. `loading` alone cannot prevent that: it is
  // set by the parent a render later, which a double-click beats.
  const [submitting, setSubmitting] = useState(false);
  const busy = loading || submitting;

  const byKey = new Map(view.canonical.map(c => [c.key, c]));
  const questions = view.open_questions.slice(0, MAX_QUESTIONS);

  // "Not sure" is the default and is a real answer meaning "leave it open" —
  // it must never be conflated with "no". Submission is enabled as soon as
  // anything is actually answered.
  const answered = Object.values(answers).filter(a => a !== 'unsure').length;

  return (
    <div className="space-y-6 animate-fade-in-up">
      <DiagnosisProgress current="questions" />

      <Card className="shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2 mb-1">
            <ListChecks className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">A few more questions</CardTitle>
          </div>
          <CardDescription>
            These are the details that best separate the conditions being considered.
            Answer only what you know, “Not sure” will leave it open.
          </CardDescription>
        </CardHeader>

        <form
          onSubmit={async e => {
            e.preventDefault();
            if (busy) return;
            setSubmitting(true);
            try {
              await onSubmit(answers);
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <CardContent className="space-y-5">
            {questions.map((key, i) => (
              <div key={key} className="space-y-2">
                <Label className="text-sm leading-relaxed">
                  <span className="text-muted-foreground font-mono mr-1.5">{i + 1}.</span>
                  {questionFor((byKey.get(key)?.plain_label || byKey.get(key)?.label || key).toLowerCase())}
                </Label>
                <RadioGroup
                  value={answers[key] ?? 'unsure'}
                  onValueChange={v => setAnswers(p => ({ ...p, [key]: v as Answer }))}
                  className="flex gap-4"
                  disabled={busy}
                >
                  {OPTIONS.map(opt => (
                    <div key={opt.value} className="flex items-center gap-1.5">
                      <RadioGroupItem value={opt.value} id={`${key}-${opt.value}`} />
                      <Label htmlFor={`${key}-${opt.value}`} className="text-sm font-normal cursor-pointer">
                        {opt.label}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            ))}

            <div className="flex gap-3 pt-1">
              <Button type="submit" disabled={busy || answered === 0} className="flex-1">
                {busy
                  ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Updating…</>
                  : `Update with ${answered} answer${answered === 1 ? '' : 's'}`}
              </Button>
              <Button type="button" variant="outline" onClick={onSkip} disabled={busy}>
                Skip and get report
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
};
