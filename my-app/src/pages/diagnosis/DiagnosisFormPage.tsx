import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Stethoscope, ChevronRight } from 'lucide-react';

interface DiagnosisFormPageProps {
  onSubmit: (symptoms: string) => Promise<void>;
  onContinue: () => void;
  loading: boolean;
  sessionId: string | null;
  workflowState: AgentState | null;
  workflowInfo?: any | null;
}

export const DiagnosisFormPage: React.FC<DiagnosisFormPageProps> = ({
  onSubmit, onContinue, loading, workflowState,
}) => {
  const [symptoms, setSymptoms] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);

  const hasDiagnosis = (workflowState?.textual_analysis ?? []).length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symptoms.trim().split(/\s+/).length < 5) {
      setInputError('Please describe your symptoms in more detail (at least a few words).');
      return;
    }
    setInputError(null);
    await onSubmit(symptoms);
  };

  if (!hasDiagnosis) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="symptoms" />
        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2 mb-1">
              <Stethoscope className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">Describe your symptoms</CardTitle>
            </div>
            <CardDescription>
              Include location, onset, severity, duration, and associated symptoms.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {inputError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{inputError}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="symptoms">Your symptoms</Label>
                <Textarea id="symptoms"
                  placeholder="e.g. Persistent headache on the right side for 3 days with nausea and light sensitivity…"
                  className="min-h-[120px] resize-none"
                  value={symptoms} onChange={e => setSymptoms(e.target.value)}
                  disabled={loading} required />
              </div>
              <p className="text-xs text-muted-foreground">
                Do not include personally identifying information such as your name or ID number.
              </p>
              <Button type="submit" className="w-full" disabled={loading || !symptoms.trim()}>
                {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analysing…</> : 'Start diagnosis'}
              </Button>
            </CardContent>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="symptoms" />
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Initial assessment complete</CardTitle>
          <CardDescription>Preliminary differential generated. Continue to check observable signs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {(workflowState!.textual_analysis ?? []).slice(0, 3).map((d, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-sm font-medium">{d.text_diagnosis}</span>
                <Badge variant={i === 0 ? 'default' : 'secondary'} className="text-xs shrink-0">
                  {Math.round(d.diagnosis_confidence * 100)}%
                </Badge>
              </div>
            ))}
          </div>
          <Button onClick={onContinue} className="w-full gap-2" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><ChevronRight className="h-4 w-4" />Continue to sign check</>}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
