import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Stethoscope, ShieldCheck } from 'lucide-react';

interface DiagnosisFormPageProps {
  onSubmit: (symptoms: string) => Promise<void>;
  loading: boolean;
}

export const DiagnosisFormPage: React.FC<DiagnosisFormPageProps> = ({ onSubmit, loading }) => {
  const [symptoms, setSymptoms] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symptoms.trim().split(/\s+/).length < 5) {
      setInputError('Please describe your symptoms in more detail (at least a few words).');
      return;
    }
    setInputError(null);
    await onSubmit(symptoms);
  };

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
            <Textarea id="symptoms"
              placeholder="e.g. Persistent headache on the right side for 3 days with nausea and light sensitivity…"
              className="min-h-[120px] resize-none"
              value={symptoms} onChange={e => setSymptoms(e.target.value)}
              disabled={loading} required />
            <div className="bg-secondary/60 rounded-lg p-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5" />
                Before you write
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                What you type is sent to an AI provider to build the medical differential. Nothing is stored as the report you download at the end is the only
                copy. Do not include your name, ID number, or contact details. See our{' '}
                <Link to="/privacy" target="_blank" className="text-primary underline underline-offset-2">
                  Privacy Policy
                </Link>{' '}and{' '}
                <Link to="/terms" target="_blank" className="text-primary underline underline-offset-2">
                  Terms
                </Link>.
              </p>
            </div>
            <Button type="submit" className="w-full" disabled={loading || !symptoms.trim()}>
              {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analysing…</> : 'Start diagnosis'}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
};
