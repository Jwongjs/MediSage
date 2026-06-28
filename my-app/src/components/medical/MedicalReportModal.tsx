import React from 'react';
import { MedicalReport } from 'services/report';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

interface MedicalReportModalProps {
  report: MedicalReport | null;
  onClose: () => void;
}

const Row: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex items-start justify-between gap-4 py-1.5">
    <span className="text-xs text-muted-foreground shrink-0 w-24">{label}</span>
    <span className="text-xs text-right">{value}</span>
  </div>
);

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="space-y-1.5">
    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{title}</p>
    {children}
  </div>
);

export const MedicalReportModal: React.FC<MedicalReportModalProps> = ({ report, onClose }) => {
  if (!report) return null;

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  const analysis = report.overall_analysis;
  const recs = report.healthcare_recommendations;

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose(); }}>
      <DialogContent className="max-w-2xl h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 shrink-0">
          <DialogTitle className="text-base leading-snug">{report.report_title}</DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6 pb-6">
          <div className="space-y-5">
            <div className="bg-secondary/40 rounded-lg p-4 space-y-0.5">
              <Row label="Created" value={formatDate(report.created_at)} />
              <Row label="Session" value={<span className="font-mono text-xs">{report.session_id}</span>} />
              <Row label="Status" value={<Badge variant="outline" className="text-xs">{report.report_status}</Badge>} />
              {analysis?.final_diagnosis && <Row label="Diagnosis" value={analysis.final_diagnosis} />}
              {analysis?.final_confidence != null && (
                <Row label="Confidence" value={`${(analysis.final_confidence * 100).toFixed(1)}%`} />
              )}
              {analysis?.specialist_recommendation && (
                <Row label="Specialist" value={analysis.specialist_recommendation.replace('_', ' ')} />
              )}
            </div>

            {report.patient_symptoms && (
              <>
                <Separator />
                <Section title="Patient Symptoms">
                  <p className="text-sm leading-relaxed">{report.patient_symptoms}</p>
                </Section>
              </>
            )}

            {analysis?.user_explanation && (
              <>
                <Separator />
                <Section title="Explanation">
                  <p className="text-sm leading-relaxed">{analysis.user_explanation}</p>
                </Section>
              </>
            )}

            {analysis?.clinical_reasoning && (
              <>
                <Separator />
                <Section title="Clinical Reasoning">
                  <p className="text-sm leading-relaxed text-muted-foreground">{analysis.clinical_reasoning}</p>
                </Section>
              </>
            )}

            {recs && (recs.immediate_actions || recs.specialist_referral) && (
              <>
                <Separator />
                <Section title="Healthcare Recommendations">
                  {recs.immediate_actions && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium">Immediate actions</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">{recs.immediate_actions}</p>
                    </div>
                  )}
                  {recs.specialist_referral && (
                    <div className="space-y-1 mt-3">
                      <p className="text-xs font-medium">Specialist referral</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">{recs.specialist_referral}</p>
                    </div>
                  )}
                </Section>
              </>
            )}

            {report.medical_report_content && (
              <>
                <Separator />
                <Section title="Full Medical Report">
                  <div className="bg-secondary/30 rounded border p-4">
                    <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed">
                      {report.medical_report_content}
                    </pre>
                  </div>
                </Section>
              </>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
