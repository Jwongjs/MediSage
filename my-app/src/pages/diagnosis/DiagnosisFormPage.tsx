import React, { useState } from 'react';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Stethoscope } from 'lucide-react';

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
};
