import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from 'components/layout/PageLayout';
import { Footer } from 'components/layout/Footer';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Brain, FileText, ShieldCheck,
  ChevronRight, Clock, ArrowRight, Stethoscope,
  MessageCircle, BookOpen,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Differential Diagnosis',
    description: 'Describe your symptoms and receive a top-5 differential with confidence scores, layman explanations, and severity assessment.',
    accent: 'text-primary bg-primary/5',
  },
  {
    icon: Stethoscope,
    title: 'Guided Sign Checks',
    description: 'Targeted prompts for the signs that separate your top candidates, then adaptive follow-up questions that sharpen the result.',
    accent: 'text-accent bg-accent/5',
  },
  {
    icon: FileText,
    title: 'Structured Reports',
    description: 'Every session ends with a downloadable report: clinical reasoning, severity, specialist recommendation, and alternatives.',
    accent: 'text-primary bg-primary/5',
  },
] as const;

const INTRO_POINTS = [
  {
    icon: MessageCircle,
    title: 'No medical degree required',
    body: 'Describe how you feel in plain words. MediSage translates it into clinical terms so you never have to look one up.',
  },
  {
    icon: BookOpen,
    title: 'Built to inform, not to diagnose',
    body: 'This is an educational first read on your symptoms, not a verdict. It helps you ask better questions, not skip a doctor.',
  },
  {
    icon: Stethoscope,
    title: 'Check-up ready',
    body: 'Bring the report to your appointment. It suggests how urgent things might be and a specialist worth seeing, so your doctor starts from what you found, not from zero.',
  },
] as const;

const STEPS = [
  { n: '01', title: 'Complete intake',        body: 'Age, medications, allergies, history — collected once, passed to every stage.' },
  { n: '02', title: 'Describe symptoms',      body: 'Natural language. The AI validates and flags vague or unsafe descriptions.' },
  { n: '03', title: 'Check observable signs', body: 'LLM-generated sign prompts targeted to your differential, then 4 adaptive follow-up questions.' },
  { n: '04', title: 'Receive your report',    body: 'Downloadable medical report with diagnosis, reasoning, severity, and next steps.' },
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
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-medium leading-[1.1] mb-2 text-foreground animate-fade-in-up"
              style={{ animationDelay: '80ms' }}
            >
              Medical clarity,
            </h1>
            <h1
              className="font-display text-4xl md:text-5xl lg:text-[3.5rem] font-medium italic leading-[1.1] mb-6 text-primary animate-fade-in-up"
              style={{ animationDelay: '160ms' }}
            >
              powered by AI.
            </h1>
            <p
              className="text-lg text-muted-foreground mb-8 leading-relaxed animate-fade-in-up"
              style={{ animationDelay: '240ms' }}
            >
              Describe your symptoms and receive a structured differential diagnosis, guided sign checks, and a downloadable medical report, in minutes.
            </p>
          </div>
          <div
            className="flex flex-col sm:flex-row justify-center gap-3 mb-8 animate-fade-in-up"
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
            className="flex flex-wrap justify-center items-center gap-x-6 gap-y-2 animate-fade-in-up"
            style={{ animationDelay: '400ms' }}
          >
            <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-primary" />No account, no sign-up
            </span>
            <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <FileText className="h-4 w-4 text-primary" />Your report downloads to your device
            </span>
            <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Clock className="h-4 w-4 text-primary" />Results in under 2 min
            </span>
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

      {/* Introduction: who MediSage is for, echoing the hero's jade wash */}
      <section className="container mx-auto max-w-6xl px-4 py-16">
        <div
          className="rounded-3xl border px-6 py-12 md:px-14 md:py-16"
          style={{ background: 'linear-gradient(135deg, hsl(160 45% 97%), hsl(var(--background)) 70%)' }}
        >
          <Badge variant="outline" className="mb-4 border-accent/30 bg-accent/10 text-accent">
            Why MediSage
          </Badge>
          <h2 className="font-display text-2xl md:text-3xl font-medium leading-snug mb-4 max-w-2xl">
            Know before you go.
          </h2>
          <p className="text-muted-foreground max-w-2xl mb-10 leading-relaxed">
            MediSage exists for people who don't speak medicine fluently. It's an educational first step, not a diagnosis, that offers a possible read on how serious things might be, suggests a specialist worth considering, and turns it all into a report your doctor can pick up on day one.
          </p>
          <div className="grid sm:grid-cols-3 gap-8">
            {INTRO_POINTS.map(({ icon: Icon, title, body }) => (
              <div key={title} className="flex flex-col gap-2">
                <Icon className="h-5 w-5 text-primary mb-1" />
                <h3 className="font-semibold text-sm">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works: same card/badge treatment as Why MediSage */}
      <section className="container mx-auto max-w-6xl px-4 py-16">
        <div
          className="rounded-3xl border px-6 py-12 md:px-14 md:py-16"
          style={{ background: 'linear-gradient(135deg, hsl(160 45% 97%), hsl(var(--background)) 70%)' }}
        >
          <Badge variant="outline" className="mb-4 border-accent/30 bg-accent/10 text-accent">
            How It Works
          </Badge>
          <h2 className="font-display text-2xl md:text-3xl font-medium leading-snug mb-4 max-w-2xl">
            Four steps to clarity.
          </h2>
          <p className="text-muted-foreground max-w-2xl mb-10 leading-relaxed">
            From your first symptom to a report ready to hand your doctor.
          </p>
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
        </div>
      </section>

      <Footer />

    </PageLayout>
  );
};

export default Homepage;
