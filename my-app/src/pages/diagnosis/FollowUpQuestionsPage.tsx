import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, ChevronRight, MessageSquare } from 'lucide-react';

interface FollowUpQuestionsPageProps {
  workflowState: AgentState | null;
  workflowInfo?: any | null;
  loading: boolean;
  onSubmitResponses: (responses: Record<string, string>) => Promise<void>;
  onContinue: () => void;
  onReset: () => void;
}

export const FollowUpQuestionsPage: React.FC<FollowUpQuestionsPageProps> = ({
  workflowState, loading, onSubmitResponses, onContinue,
}) => {
  const questions    = workflowState?.followup_questions ?? [];
  const hasResponses = (workflowState?.followup_diagnosis ?? []).length > 0;
  const [responses, setResponses] = useState<Record<string, string>>({});

  const allAnswered = questions.length > 0 && questions.every(q => (responses[q] ?? '').trim().length > 0);

  if (hasResponses) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="followup" />
        <Card className="shadow-sm text-center">
          <CardHeader>
            <CardTitle className="text-lg">Follow-up complete</CardTitle>
            <CardDescription>Responses analysed. Continue to overall analysis.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={onContinue} className="gap-2" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><ChevronRight className="h-4 w-4" />Continue to analysis</>}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="followup" />
      <Card className="shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2 mb-1">
            <MessageSquare className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Follow-up questions</CardTitle>
          </div>
          <CardDescription>Answer accurately — these are tailored to your symptom profile.</CardDescription>
        </CardHeader>
        <form onSubmit={async e => { e.preventDefault(); await onSubmitResponses(responses); }}>
          <CardContent className="space-y-5">
            {questions.map((q, i) => (
              <div key={i} className="space-y-1.5">
                <Label htmlFor={`q-${i}`} className="text-sm leading-relaxed">
                  <span className="text-muted-foreground font-mono mr-1.5">{i + 1}.</span>{q}
                </Label>
                <Textarea id={`q-${i}`} placeholder="Your answer…" className="min-h-[80px] resize-none text-sm"
                  value={responses[q] ?? ''} onChange={e => setResponses(p => ({ ...p, [q]: e.target.value }))}
                  disabled={loading} />
              </div>
            ))}
            <Button type="submit" className="w-full" disabled={loading || !allAnswered}>
              {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting…</> : 'Submit answers'}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
};
