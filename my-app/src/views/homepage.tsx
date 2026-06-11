import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Activity, Brain, FileText, MessageSquare, ShieldCheck,
  ChevronRight, Clock, ArrowRight, Stethoscope,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Differential Diagnosis',
    description: 'Describe your symptoms and receive a top-5 differential with confidence scores, layman explanations, and severity assessment.',
    accent: 'text-primary bg-primary/5',
  },
  {
    icon: MessageSquare,
    title: 'Medical History Chat',
    description: 'Ask questions about your past sessions. The assistant retrieves context from your stored diagnostic reports — no hallucination.',
    accent: 'text-accent bg-accent/5',
  },
  {
    icon: FileText,
    title: 'Structured Reports',
    description: 'Every session ends with a downloadable report: clinical reasoning, severity, specialist recommendation, and alternatives.',
    accent: 'text-primary bg-primary/5',
  },
] as const;

const STEPS = [
  { n: '01', title: 'Complete intake',        body: 'Age, medications, allergies, history — collected once, passed to every stage.' },
  { n: '02', title: 'Describe symptoms',      body: 'Natural language. The AI validates and flags vague or unsafe descriptions.' },
  { n: '03', title: 'Check observable signs', body: 'LLM-generated sign prompts targeted to your differential, then 4 adaptive follow-up questions.' },
  { n: '04', title: 'Receive your report',    body: 'Downloadable medical report with diagnosis, reasoning, severity, and next steps.' },
] as const;

const Homepage: React.FC = () => {
  const { loggedIn } = useAuth();
  const navigate = useNavigate();
  const cta = loggedIn ? '/diagnosis' : '/register';

  return (
    <PageLayout>

      {/* Hero — dark navy with diagonal clip and dot-grid texture */}
      <section
        className="relative overflow-hidden bg-[#0D1B2A]"
        style={{ clipPath: 'polygon(0 0, 100% 0, 100% 88%, 0 100%)', paddingBottom: '7rem' }}
      >
        {/* Dot-grid texture */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='1' fill='%23ffffff' fill-opacity='0.04'/%3E%3C/svg%3E")`,
          }}
        />
        {/* Sky radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 60% 50% at 70% 40%, rgba(14,165,233,0.12), transparent)' }}
        />

        <div className="container mx-auto max-w-6xl px-4 pt-20 pb-4 md:pt-28 relative z-10">
          <div className="max-w-2xl">
            <Badge
              variant="outline"
              className="mb-6 text-xs font-medium border-sky-400/30 bg-sky-400/10 text-sky-300 gap-1.5 animate-fade-in-up"
              style={{ animationDelay: '0ms' }}
            >
              <Activity className="h-3 w-3" />AI-powered medical assistant
            </Badge>
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-normal leading-[1.1] mb-2 text-white animate-fade-in-up"
              style={{ animationDelay: '80ms' }}
            >
              Medical clarity,
            </h1>
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-normal italic leading-[1.1] mb-6 text-sky-300 animate-fade-in-up"
              style={{ animationDelay: '160ms' }}
            >
              powered by AI.
            </h1>
            <p
              className="text-lg text-slate-300 mb-8 leading-relaxed animate-fade-in-up"
              style={{ animationDelay: '240ms' }}
            >
              Describe your symptoms and receive a structured differential diagnosis, guided sign checks, and a downloadable medical report — in minutes.
            </p>
            <div
              className="flex flex-col sm:flex-row gap-3 mb-8 animate-fade-in-up"
              style={{ animationDelay: '320ms' }}
            >
              <Button
                size="lg"
                className="gap-2 text-base bg-sky-500 hover:bg-sky-400 text-white border-0"
                onClick={() => navigate(cta)}
              >
                Start your assessment<ArrowRight className="h-4 w-4" />
              </Button>
              {!loggedIn && (
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10 hover:text-white"
                  asChild
                >
                  <Link to="/login">Sign in</Link>
                </Button>
              )}
            </div>
            <div
              className="flex flex-wrap items-center gap-x-6 gap-y-2 animate-fade-in-up"
              style={{ animationDelay: '400ms' }}
            >
              <span className="flex items-center gap-1.5 text-sm text-slate-400">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />No real PHI stored
              </span>
              <span className="flex items-center gap-1.5 text-sm text-slate-400">
                <Clock className="h-4 w-4 text-emerald-400" />Results in under 2 min
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Features — overlap the diagonal cut */}
      <section className="container mx-auto max-w-6xl px-4 -mt-12 relative z-10 pb-16">
        <div className="grid md:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, description, accent }) => (
            <Card key={title} className="border shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${accent}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <div className="container mx-auto max-w-6xl px-4"><Separator /></div>

      {/* How it works */}
      <section className="container mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl md:text-3xl font-bold mb-2">How it works</h2>
        <p className="text-muted-foreground mb-10">Four steps from first symptom to structured report.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {STEPS.map(({ n, title, body }, i) => (
            <div key={n} className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <span className="text-3xl font-bold text-primary/20 font-mono tabular-nums">{n}</span>
                {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-border hidden lg:block ml-auto" />}
              </div>
              <h3 className="font-semibold">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary/5 border-t border-primary/10">
        <div className="container mx-auto max-w-6xl px-4 py-16 flex flex-col items-center text-center gap-4">
          <Stethoscope className="h-10 w-10 text-primary" />
          <h2 className="text-2xl md:text-3xl font-bold">Ready to start?</h2>
          <p className="text-muted-foreground max-w-md">
            Create a free account and run your first diagnostic assessment in under two minutes.
          </p>
          <Button size="lg" onClick={() => navigate(cta)} className="gap-2 mt-2">
            {loggedIn ? 'Go to diagnosis' : 'Create free account'}<ArrowRight className="h-4 w-4" />
          </Button>
          <p className="text-xs text-muted-foreground">
            For educational purposes only. Not a substitute for professional medical advice.
          </p>
        </div>
      </section>

    </PageLayout>
  );
};

export default Homepage;
