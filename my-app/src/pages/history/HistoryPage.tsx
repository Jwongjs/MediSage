import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Trash2, Clock } from 'lucide-react';
import { PageLayout } from 'components/layout/PageLayout';
import { DiagnosisService } from 'services/diagnosis';
import { HistoryEntry } from 'types/diagnosis';

export const HistoryPage: React.FC = () => {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setEntries((await DiagnosisService.history()).sessions);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load history');
    }
  };

  useEffect(() => { load(); }, []);

  // Hard delete with no undo, so confirm first. Without the try/catch a
  // failed DELETE rejects unhandled and the row just silently stays put.
  const remove = async (entry: HistoryEntry) => {
    if (!window.confirm(`Delete "${entry.title}"? This cannot be undone.`)) return;
    setError(null);
    try {
      await DiagnosisService.deleteHistory(entry.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not delete that session');
    }
  };

  return (
    <PageLayout className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="font-display text-2xl mb-1">Diagnosis history</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Every session you have saved. Deleting one removes it permanently.
      </p>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {entries === null && !error && (
        <div className="space-y-3">
          {[0, 1, 2].map(i => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      )}

      {entries?.length === 0 && (
        <Card className="shadow-sm">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No saved sessions yet.
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {entries?.map(entry => (
          <Card key={entry.id} className="shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-base font-display">{entry.title}</CardTitle>
                  <CardDescription className="text-xs flex items-center gap-1 mt-1">
                    <Clock className="h-3 w-3" />
                    {new Date(entry.created_at).toLocaleString()}
                  </CardDescription>
                </div>
                <Button
                  variant="ghost" size="sm"
                  onClick={() => remove(entry)}
                  aria-label={`Delete ${entry.title}`}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </PageLayout>
  );
};
