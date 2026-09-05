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
        <h1 className="font-display text-4xl font-medium">Privacy Policy</h1>
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
        <p><strong className="text-foreground">Health information you submit</strong> — symptom descriptions and follow-up answers you enter when requesting diagnostic suggestions.</p>
        <p><strong className="text-foreground">Session state</strong> — your answers and the generated analysis are held against a randomly generated session identifier so the assessment can move from one step to the next. The session is not linked to any account, and we do not ask for your name, email, or contact details.</p>
        <p><strong className="text-foreground">Diagnostic reports</strong> — the report is generated for your session and downloaded to your own device. We do not keep a copy in an account, because MediSage has no accounts.</p>
        <p><strong className="text-foreground">Technical data</strong> — we do not use advertising or cross-site tracking cookies.</p>
      </Section>

      <Section title="3. Health data is special category data">
        <p>
          Health-related information is special category personal data under Article 9 of the
          GDPR and sensitive personal data under Malaysia's Personal Data Protection Act 2010.
          We process it on the basis of your explicit consent, given when you submit symptoms
          for assessment. You may withdraw that consent at any time by stopping use of the
          Service and contacting us to request deletion of the session data described above.
        </p>
      </Section>

      <Section title="4. How we use your data">
        <p>We use the data you provide to:</p>
        <ul className="list-disc pl-5 space-y-1.5">
          <li>generate differential-diagnosis suggestions and follow-up questions;</li>
          <li>carry your answers between the steps of a single assessment.</li>
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
          <li><strong className="text-foreground">Supabase</strong> — encrypted database storage of assessment session state.</li>
        </ul>
        <p>
          Because symptom text is processed by an AI provider, do not include personally
          identifying details — your name, identification numbers, addresses, or contact
          information — in symptom descriptions.
        </p>
      </Section>

      <Section title="6. Security and retention">
        <p>
          Data is encrypted in transit (TLS) and at rest. Because there are no accounts,
          the only data we hold is the session state described in section 2, retained so an
          in-progress assessment can be completed. Deletion of a session's data can be
          requested by email and is processed without undue delay.
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
        <p>You can exercise these rights by contacting us by email.</p>
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
