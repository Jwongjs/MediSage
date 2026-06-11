import React from 'react';
import { Navbar } from './Navbar';

interface PageLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const PageLayout: React.FC<PageLayoutProps> = ({ children, className }) => (
  <div className="min-h-screen bg-background flex flex-col">
    <Navbar />
    <main className={`flex-1 ${className ?? ''}`}>{children}</main>
  </div>
);
