import React from 'react';
import { Link } from 'react-router-dom';
import { PageLayout } from 'components/layout/PageLayout';
import { Footer } from 'components/layout/Footer';
import { Separator } from '@/components/ui/separator';

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section className="space-y-3">
    <h2 className="text-lg font-semibold">{title}</h2>
    <div className="space-y-3 text-sm text-muted-foreground leading-relaxed">{children}</div>
  </section>
);

const TermsPage: React.FC = () => (
  <PageLayout>
    <div className="container mx-auto max-w-3xl px-4 py-12 space-y-8">
      <header className="space-y-2">
        <h1 className="font-display text-4xl font-normal">Terms of Service</h1>
        <p className="text-sm text-muted-foreground">Last updated: 12 June 2026</p>
      </header>

      <Separator />

      <Section title="1. Acceptance of these terms">
        <p>
          These Terms of Service ("Terms") govern your use of MediSage (the "Service"). By creating
          an account or using the Service, you confirm that you have read, understood, and agree to
          be bound by these Terms and by our{' '}
          <Link to="/privacy" className="text-primary underline underline-offset-2">Privacy Policy</Link>.
          If you do not agree, do not use the Service.
        </p>
      </Section>

      <Section title="2. What MediSage is — and is not">
        <p>
          MediSage is an <strong className="text-foreground">educational, AI-assisted information tool</strong>.
          It generates possible explanations for symptoms you describe and produces an informational
          report. It is <strong className="text-foreground">not a certified or registered medical
          device</strong>, and it has not undergone clinical validation or regulatory conformity assessment.
        </p>
        <p>
          The Service does <strong className="text-foreground">not</strong> provide medical advice,
          diagnosis, or treatment, and using it does <strong className="text-foreground">not</strong>{' '}
          create a doctor–patient relationship between you and MediSage or anyone associated with it.
        </p>
      </Section>

      <Section title="3. Not for emergencies">
        <p>
          MediSage must never be used for medical emergencies. If you think you may have a medical
          emergency, or your symptoms are severe or rapidly worsening, contact your local emergency
          services or go to the nearest emergency department immediately. Do not delay seeking
          professional care because of anything you read on the Service.
        </p>
      </Section>

      <Section title="4. Eligibility">
        <p>
          You must be at least 18 years old, or use the Service under the supervision of a parent or
          legal guardian who accepts these Terms on your behalf. You are responsible for providing
          accurate account information.
        </p>
      </Section>

      <Section title="5. Your responsibilities">
        <ul className="list-disc pl-5 space-y-1.5">
          <li>Provide truthful information; inaccurate input produces unreliable output.</li>
          <li>
            Do not enter personally identifying information — your name, identification numbers,
            addresses, or contact details — into symptom fields, as this text is processed by a
            third-party AI provider.
          </li>
          <li>Use the Service only for lawful, personal, non-commercial purposes.</li>
          <li>
            Do not rely on the Service as a substitute for professional medical judgment, and always
            consult a qualified healthcare professional before making health decisions.
          </li>
        </ul>
      </Section>

      <Section title="6. Assumption of risk">
        <p>
          AI systems can produce information that is incomplete, outdated, or incorrect. You
          understand and accept that any reliance you place on the Service's output is at your own
          risk, and that you remain solely responsible for any decisions you make about your health.
        </p>
      </Section>

      <Section title="7. Your data and saved reports">
        <p>
          Our handling of your personal and health data is described in the{' '}
          <Link to="/privacy" className="text-primary underline underline-offset-2">Privacy Policy</Link>.
          Diagnostic reports are stored only when you explicitly choose to save them, and you may
          delete them from your profile at any time.
        </p>
      </Section>

      <Section title="8. Intellectual property">
        <p>
          The Service, including its software, design, and content, is owned by MediSage and protected
          by applicable intellectual-property laws. The informational report generated from your own
          input is yours to keep and use for personal purposes.
        </p>
      </Section>

      <Section title="9. Disclaimer of warranties">
        <p>
          The Service is provided <strong className="text-foreground">"as is" and "as available"</strong>,
          without warranties of any kind, whether express or implied, including any warranty of
          accuracy, fitness for a particular purpose, or non-infringement. We do not warrant that the
          Service will be uninterrupted, error-free, or that its output is accurate or complete.
        </p>
      </Section>

      <Section title="10. Limitation of liability">
        <p>
          To the fullest extent permitted by law, MediSage and its creators shall not be liable for
          any indirect, incidental, special, consequential, or punitive damages, or for any loss
          arising from your use of, or inability to use, the Service — including any health outcome,
          decision, or action taken in reliance on its output. Nothing in these Terms excludes
          liability that cannot be excluded under applicable law.
        </p>
      </Section>

      <Section title="11. Indemnification">
        <p>
          You agree to indemnify and hold harmless MediSage and its creators from any claim or demand
          arising out of your misuse of the Service or your breach of these Terms.
        </p>
      </Section>

      <Section title="12. Changes to the Service and these Terms">
        <p>
          We may modify or discontinue the Service, or update these Terms, at any time. Significant
          changes will be announced within the MediSage interface. Continued use after changes take
          effect constitutes acceptance of the revised Terms.
        </p>
      </Section>

      <Section title="13. Governing law">
        <p>
          These Terms are governed by the laws of Malaysia, without regard to conflict-of-law
          principles. Where you use the Service from another jurisdiction, you remain responsible for
          compliance with local law.
        </p>
      </Section>

      <Section title="14. Contact">
        <p>
          Questions about these Terms can be sent to{' '}
          <a href="mailto:justin20wjs@gmail.com" className="text-primary underline underline-offset-2">
            justin20wjs@gmail.com
          </a>.
        </p>
      </Section>
    </div>
    <Footer />
  </PageLayout>
);

export default TermsPage;
