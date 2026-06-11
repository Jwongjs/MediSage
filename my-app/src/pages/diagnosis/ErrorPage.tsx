import React from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface ErrorPageProps {
  error: string;
  onReset: () => void;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({ error, onReset }) => (
  <div className="max-w-md mx-auto space-y-4 py-8">
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
    </Alert>
    <Button variant="outline" onClick={onReset} className="gap-2">
      <RotateCcw className="h-4 w-4" />Start over
    </Button>
  </div>
);
