import React from 'react';
import { PageLayout } from 'components/layout/PageLayout';
import { ChatPanel } from 'components/medical/ChatPanel';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck } from 'lucide-react';

const ChatbotPage: React.FC = () => (
  <PageLayout>
    <div className="container mx-auto max-w-3xl px-4 py-8 flex flex-col" style={{ height: 'calc(100vh - 3.5rem)' }}>
      <div className="mb-4 shrink-0">
        <h1 className="text-xl font-bold">Health Assistant</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Powered by your diagnostic history and uploaded medical reports.
        </p>
      </div>
      <div className="mb-4 shrink-0">
        <Badge variant="outline" className="text-xs gap-1.5">
          <ShieldCheck className="h-3 w-3 text-accent" />Answers from your records only
        </Badge>
      </div>
      <div className="flex-1 min-h-0">
        <ChatPanel />
      </div>
      <p className="text-xs text-center text-muted-foreground mt-3 shrink-0">
        This assistant cannot diagnose new symptoms. Use the{' '}
        <a href="/diagnosis" className="text-primary hover:underline">Diagnosis</a> tool for new assessments.
      </p>
    </div>
  </PageLayout>
);

export default ChatbotPage;
