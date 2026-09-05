import React from 'react';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';

export const Footer: React.FC = () => (
  <footer className="border-t bg-secondary/40">
    <div className="container mx-auto max-w-6xl px-4 py-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <Activity className="h-4 w-4 text-primary" />
          <span className="font-bold tracking-tight">MediSage</span>
        </div>
        <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
          AI-assisted health guidance. For educational purposes only — not a substitute
          for professional medical advice, diagnosis, or treatment.
        </p>
      </div>
      <nav className="flex items-center gap-6 text-sm">
        <Link to="/terms" className="text-muted-foreground hover:text-primary transition-colors">
          Terms of Service
        </Link>
        <Link to="/privacy" className="text-muted-foreground hover:text-primary transition-colors">
          Privacy Policy
        </Link>
        <a href="mailto:justin20wjs@gmail.com" className="text-muted-foreground hover:text-primary transition-colors">
          Contact
        </a>
      </nav>
    </div>
    <div className="border-t">
      <div className="container mx-auto max-w-6xl px-4 py-4">
        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} MediSage. All rights reserved.
        </p>
      </div>
    </div>
  </footer>
);
