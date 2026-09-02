import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Activity, Stethoscope } from 'lucide-react';

export const Navbar: React.FC = () => (
  <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
    <div className="container mx-auto flex h-14 max-w-6xl items-center justify-between px-4">

      <Link to="/" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
        <Activity className="h-5 w-5 text-primary" />
        <span className="font-bold text-lg tracking-tight">MediSage</span>
      </Link>

      <Button size="sm" asChild>
        <Link to="/diagnosis"><Stethoscope className="h-4 w-4 mr-1.5" />Start assessment</Link>
      </Button>

    </div>
  </header>
);

export default Navbar;
