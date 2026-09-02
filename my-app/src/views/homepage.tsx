import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from 'components/layout/PageLayout';
import { Footer } from 'components/layout/Footer';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Activity, Brain, FileText, ShieldCheck,
  ChevronRight, Clock, ArrowRight, Stethoscope,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Differential Diagnosis',
    description: 'Describe your symptoms and receive a ranked differential showing which criteria each condition is supported or contradicted by.',
    accent: 'text-primary bg-primary/5',
  },
  {
    icon: ShieldCheck,
    title: 'No Account, Nothing Stored',
    description: 'There is no sign-up and no database. A session lives only while you have it open — the report you download is the only copy.',
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
  { n: '01', title: 'Describe symptoms',      body: 'Natural language. The AI validates and flags vague or unsafe descriptions.' },
  { n: '02', title: 'Check observable signs', body: 'Sign prompts targeted to your differential, then follow-up questions that separate the candidates.' },
  { n: '03', title: 'Download your report',   body: 'A report with the differential, the evidence behind it, severity, and next steps.' },
] as const;

const Homepage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageLayout>

      {/* Hero — light jade wash with dot-vector texture */}
      <section className="relative overflow-hidden">
        {/* Soft jade wash fading into the page background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'linear-gradient(180deg, hsl(160 45% 95%), hsl(var(--background)))' }}
        />
        {/* Dot-vector texture, fading toward the bottom */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(circle, hsl(var(--primary) / 0.18) 1.5px, transparent 1.5px)',
            backgroundSize: '26px 26px',
            maskImage: 'radial-gradient(ellipse 90% 95% at 70% 0%, black 25%, transparent 72%)',
            WebkitMaskImage: 'radial-gradient(ellipse 90% 95% at 70% 0%, black 25%, transparent 72%)',
          }}
        />
        {/* Jade radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 55% 50% at 75% 30%, hsl(var(--accent) / 0.10), transparent)' }}
        />

        <div className="container mx-auto max-w-6xl px-4 pt-20 pb-28 md:pt-28 relative z-10">
          <div className="max-w-2xl">
            <Badge
              variant="outline"
              className="mb-6 text-xs font-medium border-primary/25 bg-primary/10 text-primary gap-1.5 animate-fade-in-up"
              style={{ animationDelay: '0ms' }}
            >
              <Activity className="h-3 w-3" />AI-powered medical assistant
            </Badge>
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-normal leading-[1.1] mb-2 text-foreground animate-fade-in-up"
              style={{ animationDelay: '80ms' }}
            >
              Medical clarity,
            </h1>
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-normal italic leading-[1.1] mb-6 text-primary animate-fade-in-up"
              style={{ animationDelay: '160ms' }}
            >
              powered by AI.
            </h1>
            <p
              className="text-lg text-muted-foreground mb-8 leading-relaxed animate-fade-in-up"
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
                className="gap-2 text-base"
                onClick={() => navigate('/diagnosis')}
              >
                Start your assessment<ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            <div
              className="flex flex-wrap items-center gap-x-6 gap-y-2 animate-fade-in-up"
              style={{ animationDelay: '400ms' }}
            >
              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <ShieldCheck className="h-4 w-4 text-primary" />No account — nothing is stored
              </span>
              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <FileText className="h-4 w-4 text-primary" />Report downloaded, not saved
              </span>
              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Clock className="h-4 w-4 text-primary" />Results in under 2 min
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
        <p className="text-muted-foreground mb-10">Three steps from first symptom to downloaded report.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
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
            Run a diagnostic assessment in under two minutes. No sign-up required.
          </p>
          <Button size="lg" onClick={() => navigate('/diagnosis')} className="gap-2 mt-2">
            Start your assessment<ArrowRight className="h-4 w-4" />
          </Button>
          <p className="text-xs text-muted-foreground">
            For educational purposes only. Not a substitute for professional medical advice.
          </p>
        </div>
      </section>

      <Footer />

    </PageLayout>
  );
};

export default Homepage;
