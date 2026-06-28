import React from 'react';
import { Link } from 'react-router-dom';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ShieldCheck, Stethoscope, Lock, FileText } from 'lucide-react';

interface PrivacyPolicyModalProps {
  onAccept: () => Promise<void>;
  onCancel: () => void;
}

const POINTS = [
  {
    icon: Stethoscope,
    title: 'Not medical advice',
    body: 'MediSage is an educational AI tool. Its suggestions are not a diagnosis and never replace a qualified doctor.',
  },
  {
    icon: Lock,
    title: 'Your symptoms are processed by AI',
    body: 'Symptom text is sent to our AI provider (Groq) to generate guidance. Never include your name, ID numbers, or contact details.',
  },
  {
    icon: FileText,
    title: 'You control your reports',
    body: 'Diagnostic reports are stored in your account only when you choose to save them — and you can delete them anytime.',
  },
] as const;

export const PrivacyPolicyModal: React.FC<PrivacyPolicyModalProps> = ({ onAccept, onCancel }) => {
  const [accepting, setAccepting] = React.useState(false);
  const [agreed, setAgreed] = React.useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try { await onAccept(); } finally { setAccepting(false); }
  };

  return (
    <Dialog open onOpenChange={open => { if (!open) onCancel(); }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <DialogTitle className="text-center text-xl">Before you begin</DialogTitle>
          <DialogDescription className="text-center">
            Please review how MediSage works and handles your health information.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2.5">
          {POINTS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex gap-3 rounded-lg border bg-secondary/40 p-3">
              <Icon className="h-4 w-4 text-primary mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium leading-tight mb-0.5">{title}</p>
                <p className="text-xs text-muted-foreground leading-relaxed">{body}</p>
              </div>
            </div>
          ))}
        </div>

        <label className="flex items-start gap-2.5 rounded-lg border border-primary/30 bg-primary/5 p-3 cursor-pointer">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 accent-primary cursor-pointer"
            checked={agreed}
            onChange={e => setAgreed(e.target.checked)}
          />
          <span className="text-sm leading-snug">
            I have read and agree to the{' '}
            <Link to="/terms" target="_blank" className="text-primary underline underline-offset-2">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" target="_blank" className="text-primary underline underline-offset-2">
              Privacy Policy
            </Link>, and understand MediSage does not provide medical advice.
          </span>
        </label>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={onCancel} disabled={accepting}>Cancel</Button>
          <Button onClick={handleAccept} disabled={accepting || !agreed}>
            {accepting ? 'Saving…' : 'Agree & start assessment'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
