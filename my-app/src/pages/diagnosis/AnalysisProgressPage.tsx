import React from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, ChevronRight, Brain } from 'lucide-react';

interface AnalysisProgressPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
  onContinue: () => void;
}

export const AnalysisProgressPage: React.FC<AnalysisProgressPageProps> = ({
  workflowState, loading, onContinue,
}) => {
  const isProcessing = loading || workflowState?.current_workflow_stage === 'performing_overall_analysis';

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="analysis" />
      <Card className="shadow-sm text-center">
        <CardHeader>
          <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-2">
            {isProcessing
              ? <Loader2 className="h-7 w-7 text-primary animate-spin" />
              : <Brain className="h-7 w-7 text-primary" />}
          </div>
          <CardTitle className="text-lg">
            {isProcessing ? 'Analysing your responses…' : 'Analysis complete'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
            {isProcessing
              ? 'The AI is integrating your symptoms, signs, and follow-up answers. This usually takes a few seconds.'
              : 'All data processed. Continue to generate your medical report.'}
          </p>
          {!isProcessing && (
            <Button onClick={onContinue} className="gap-2">
              <ChevronRight className="h-4 w-4" />Continue to report
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
