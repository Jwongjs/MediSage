import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, FileText, RotateCcw, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FinalReportPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
}

const SEVERITY_CLASS: Record<string, string> = {
  mild:      'severity-mild',
  moderate:  'severity-moderate',
  severe:    'severity-severe',
  critical:  'severity-critical',
  emergency: 'severity-critical',
};

export const FinalReportPage: React.FC<FinalReportPageProps> = ({
  workflowState, loading, onReset,
}) => {
  const [reportOpen, setReportOpen] = useState(false);

  if (loading || !workflowState?.overall_analysis) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="report" />
        <Card className="shadow-sm text-center">
          <CardContent className="py-12 space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-sm text-muted-foreground">Generating your medical report…</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const analysis   = workflowState.overall_analysis;
  const severity   = (analysis.final_severity ?? 'mild').toLowerCase();
  const isCritical = severity === 'critical' || severity === 'emergency';
  const alts = (workflowState.followup_diagnosis?.length ?? 0) > 1
    ? workflowState.followup_diagnosis!.slice(1, 4)
    : (workflowState.textual_analysis ?? []).slice(1, 4);

  return (
    <div className="space-y-6 animate-fade-in-up">
      <DiagnosisProgress current="report" />

      {isCritical && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Emergency — seek immediate care</AlertTitle>
          <AlertDescription>
            One or more symptoms may indicate a life-threatening condition. Call 911 or go to the nearest emergency room immediately.
          </AlertDescription>
        </Alert>
      )}

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <CardDescription className="text-xs mb-1">Primary diagnosis</CardDescription>
              <CardTitle className="text-xl">{analysis.final_diagnosis}</CardTitle>
            </div>
            <Badge className={cn('text-xs', SEVERITY_CLASS[severity] ?? SEVERITY_CLASS.mild)}>
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {analysis.user_explanation && (
            <div className="bg-secondary/60 rounded-lg p-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">What this means</p>
              <p className="text-sm leading-relaxed">{analysis.user_explanation}</p>
            </div>
          )}
          {analysis.clinical_reasoning && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">Clinical reasoning</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{analysis.clinical_reasoning}</p>
            </div>
          )}
          {analysis.specialist_recommendation && (
            <>
              <Separator />
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Recommended specialist</p>
                <Badge variant="outline" className="text-xs">{analysis.specialist_recommendation}</Badge>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {alts.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Alternative diagnoses considered</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alts.map((d, i) => {
              const pct = Math.round(d.diagnosis_confidence * 100);
              return (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{d.text_diagnosis}</span>
                    <span className="text-muted-foreground text-xs">{pct}%</span>
                  </div>
                  <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-primary/50 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        {workflowState.medical_report && (
          <Button variant="outline" className="gap-2 flex-1" onClick={() => setReportOpen(r => !r)}>
            <FileText className="h-4 w-4" />{reportOpen ? 'Hide' : 'View'} full report
          </Button>
        )}
        <Button variant="outline" onClick={onReset} className="gap-2 flex-1">
          <RotateCcw className="h-4 w-4" />New diagnosis
        </Button>
      </div>

      {reportOpen && workflowState.medical_report && (
        <Card className="shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Full Medical Report</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96 w-full rounded border bg-secondary/30">
              <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed p-4">
                {workflowState.medical_report}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-center text-muted-foreground">
        AI-generated for informational purposes only. Not a medical diagnosis. Always consult a qualified healthcare professional.
      </p>
    </div>
  );
};
