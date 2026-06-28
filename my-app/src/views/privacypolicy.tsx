import React from 'react';
import { PageLayout } from 'components/layout/PageLayout';
import { Footer } from 'components/layout/Footer';
import { Separator } from '@/components/ui/separator';

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section className="space-y-3">
    <h2 className="text-lg font-semibold">{title}</h2>
    <div className="space-y-3 text-sm text-muted-foreground leading-relaxed">{children}</div>
  </section>
);

const PrivacyPolicyPage: React.FC = () => (
  <PageLayout>
    <div className="container mx-auto max-w-3xl px-4 py-12 space-y-8">
      <header className="space-y-2">
        <h1 className="font-display text-4xl font-normal">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground">Last updated: 12 June 2026</p>
      </header>

      <Separator />

      <Section title="1. Who we are">
        <p>
          MediSage ("we", "our", "us") is an AI-assisted health guidance platform. We act as
          the data controller for the personal data processed through this service.
        </p>
        <p>
          For any privacy enquiry or request, contact us at{' '}
          <a href="mailto:justin20wjs@gmail.com" className="text-primary underline underline-offset-2">
            justin20wjs@gmail.com
          </a>.
        </p>
      </Section>

      <Section title="2. Information we collect">
        <p><strong className="text-foreground">Account information</strong> — your email address, age, and gender, provided when you register.</p>
        <p><strong className="text-foreground">Health information you submit</strong> — symptom descriptions and follow-up answers you enter when requesting diagnostic suggestions.</p>
        <p><strong className="text-foreground">Diagnostic reports</strong> — generated reports are stored in your account <em>only when you choose to save them</em>. You can view and delete them from your profile at any time.</p>
        <p><strong className="text-foreground">Technical data</strong> — an authentication cookie (httpOnly) used to keep you signed in. We do not use advertising or cross-site tracking cookies.</p>
      </Section>

      <Section title="3. Health data is special category data">
        <p>
          Health-related information is special category personal data under Article 9 of the
          GDPR and sensitive personal data under Malaysia's Personal Data Protection Act 2010.
          We process it only with your explicit consent, which we ask for before your first
          assessment and which you may withdraw at any time.
        </p>
      </Section>

      <Section title="4. How we use your data">
        <p>We use the data you provide to:</p>
        <ul className="list-disc pl-5 space-y-1.5">
          <li>generate differential-diagnosis suggestions and follow-up questions;</li>
          <li>answer your questions in the history chat, using only your saved reports;</li>
          <li>maintain your account and session.</li>
        </ul>
        <p>
          We do not sell, rent, or share your personal data with third parties for marketing
          or any unrelated purpose.
        </p>
      </Section>

      <Section title="5. Service providers">
        <p>To provide the service, your data is processed by:</p>
        <ul className="list-disc pl-5 space-y-1.5">
          <li><strong className="text-foreground">Groq</strong> — symptom text is sent to Groq's AI infrastructure to generate diagnostic suggestions;</li>
          <li><strong className="text-foreground">Supabase</strong> — authentication and encrypted storage of your account and saved reports.</li>
        </ul>
        <p>
          Because symptom text is processed by an AI provider, do not include personally
          identifying details — your name, identification numbers, addresses, or contact
          information — in symptom descriptions.
        </p>
      </Section>

      <Section title="6. Security and retention">
        <p>
          Data is encrypted in transit (TLS) and at rest. Authentication uses httpOnly
          cookies. Saved reports are retained until you delete them from your profile;
          account deletion can be requested by email and is processed without undue delay.
        </p>
      </Section>

      <Section title="7. Your rights">
        <p>Subject to applicable law (GDPR / PDPA), you have the right to:</p>
        <ul className="list-disc pl-5 space-y-1.5">
          <li>access the personal data we hold about you;</li>
          <li>correct inaccurate or incomplete data;</li>
          <li>delete your data ("right to be forgotten");</li>
          <li>withdraw consent at any time, without affecting prior lawful processing;</li>
          <li>lodge a complaint with your local supervisory authority.</li>
        </ul>
        <p>You can exercise these rights from your profile page or by contacting us by email.</p>
      </Section>

      <Section title="8. Not medical advice">
        <p>
          MediSage is an educational tool and is not a certified medical device. Its output
          is not a medical diagnosis and must not be relied upon as a substitute for
          professional medical advice, diagnosis, or treatment. If you believe you are
          experiencing a medical emergency, contact your local emergency services immediately.
        </p>
      </Section>

      <Section title="9. Changes to this policy">
        <p>
          We may update this policy periodically. Significant changes will be announced in
          the MediSage interface. The "Last updated" date above indicates the latest revision.
        </p>
      </Section>
    </div>
    <Footer />
  </PageLayout>
);

export default PrivacyPolicyPage;
