import React, { useState } from 'react';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Loader2, RotateCcw, AlertTriangle, ExternalLink,
  Download, FileText, FileType, AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { DiagnosisService } from 'services/diagnosis';
import { DiagnosisView, ExportFormat } from 'types/diagnosis';

interface FinalReportPageProps {
  view: DiagnosisView;
  loading: boolean;
  sessionId: string | null;
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

export const FinalReportPage: React.FC<FinalReportPageProps> = ({
  view, loading, sessionId, onReset,
}) => {
  // Which format is in flight, so only that button spins while both disable.
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Resetting drops the session id, which is the only handle on the report.
  // Nothing is stored, so an accidental click is unrecoverable.
  const handleReset = () => {
    const confirmed = window.confirm(
      'Start a new diagnosis? This report is not saved anywhere — if you have not downloaded it, it will be gone.'
    );
    if (confirmed) onReset();
  };

  const handleExport = async (format: ExportFormat) => {
    if (!sessionId) return;
    setExporting(format);
    setExportError(null);
    try {
      await DiagnosisService.exportReport(sessionId, format);
    } catch (error) {
      setExportError(
        error instanceof Error ? error.message : 'Could not build the file. Please try again.'
      );
    } finally {
      setExporting(null);
    }
  };

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

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2 mb-1">
            <Download className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Take this with you</CardTitle>
          </div>
          <CardDescription>
            Nothing from this session is stored — the file you download is the only copy.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {exportError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{exportError}</AlertDescription>
            </Alert>
          )}
          <div className="bg-secondary/60 rounded-lg p-4 space-y-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Download format
            </p>
            <div className="flex gap-3 flex-wrap">
              <Button
                className="gap-2 flex-1"
                disabled={!sessionId || exporting !== null}
                onClick={() => handleExport('pdf')}
              >
                {exporting === 'pdf'
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <FileText className="h-4 w-4" />}
                PDF
              </Button>
              <Button
                variant="outline"
                className="gap-2 flex-1"
                disabled={!sessionId || exporting !== null}
                onClick={() => handleExport('word')}
              >
                {exporting === 'word'
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <FileType className="h-4 w-4" />}
                Word
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button variant="outline" onClick={handleReset} className="gap-2 w-full">
        <RotateCcw className="h-4 w-4" />New diagnosis
      </Button>

      <p className="text-xs text-center text-muted-foreground">
        AI-generated for informational purposes only. Not a medical diagnosis. Always consult a qualified healthcare professional.
      </p>
    </div>
  );
};
