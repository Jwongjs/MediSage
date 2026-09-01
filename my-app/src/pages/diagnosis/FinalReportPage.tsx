import React from 'react';
import { Link } from 'react-router-dom';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { useAuth } from 'contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, RotateCcw, AlertTriangle, CheckCircle2, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DiagnosisView } from 'types/diagnosis';

interface FinalReportPageProps {
  view: DiagnosisView;
  loading: boolean;
  onReset: () => void;
}

// An unmatched severity falls back to `severity-unknown`, never `severity-mild`:
// the backend emits "unknown" deliberately when severity is unparseable, and
// styling that as mild would fail toward reassurance.
const SEVERITY_CLASS: Record<string, string> = {
  mild:     'severity-mild',
  moderate: 'severity-moderate',
  severe:   'severity-severe',
  critical: 'severity-critical',
  unknown:  'severity-unknown',
};

export const FinalReportPage: React.FC<FinalReportPageProps> = ({ view, loading, onReset }) => {
  const { loggedIn } = useAuth();

  if (loading || !view.summary) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="summary" />
        <Card className="shadow-sm text-center">
          <CardContent className="py-12 space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-sm text-muted-foreground">Preparing your summary…</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const summary    = view.summary;
  const severity   = (summary.severity ?? 'unknown').toLowerCase();
  const isCritical = severity === 'critical';
  const primary    = view.ranking[0]?.diagnoses[0];
  const alts       = view.ranking.flatMap(g => g.diagnoses).slice(1, 4);

  return (
    <div className="space-y-6 animate-fade-in-up">
      <DiagnosisProgress current="summary" />

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
              <CardDescription className="text-xs mb-1">Best-supported condition</CardDescription>
              <CardTitle className="text-xl">{primary ?? 'No condition could be assessed'}</CardTitle>
            </div>
            <Badge className={cn('text-xs', SEVERITY_CLASS[severity] ?? SEVERITY_CLASS.unknown)}>
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {summary.user_explanation && (
            <div className="bg-secondary/60 rounded-lg p-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">What this means</p>
              <p className="text-sm leading-relaxed">{summary.user_explanation}</p>
              {summary.explanation_source && (
                <p className="text-xs text-muted-foreground mt-2.5">
                  Source: {summary.explanation_url ? (
                    <a href={summary.explanation_url} target="_blank" rel="noreferrer"
                      className="text-primary underline underline-offset-2 inline-flex items-center gap-1">
                      {summary.explanation_source}<ExternalLink className="h-3 w-3" />
                    </a>
                  ) : summary.explanation_source}
                </p>
              )}
            </div>
          )}
          {summary.specialist_recommendation && (
            <>
              <Separator />
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Recommended specialist</p>
                <Badge variant="outline" className="text-xs">{summary.specialist_recommendation}</Badge>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {alts.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Alternative conditions considered</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alts.map(name => (
              <div key={name} className="text-sm font-medium py-2 border-b last:border-0">{name}</div>
            ))}
          </CardContent>
        </Card>
      )}

      {loggedIn && (
        <div className="flex items-start gap-2.5 rounded-lg bg-secondary/60 p-4">
          <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
          <p className="text-sm text-muted-foreground leading-relaxed">
            This session is saved to your{' '}
            <Link to="/history" className="text-primary underline underline-offset-2">history</Link>.
            You can delete it there at any time — deletion is permanent.
          </p>
        </div>
      )}

      <Button variant="outline" onClick={onReset} className="gap-2 w-full">
        <RotateCcw className="h-4 w-4" />New diagnosis
      </Button>

      <p className="text-xs text-center text-muted-foreground">
        AI-generated for informational purposes only. Not a medical diagnosis. Always consult a qualified healthcare professional.
      </p>
    </div>
  );
};
