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
        <p className="text-sm text-muted-foreground">Last updated: 2 September 2026</p>
      </header>

      <Separator />

      <Section title="1. Who we are">
        <p>
          MediSage ("we", "our", "us") is an AI-assisted health guidance tool. This policy
          describes what happens to the text you type into it.
        </p>
        <p>
          For any privacy enquiry, contact us at{' '}
          <a href="mailto:justin20wjs@gmail.com" className="text-primary underline underline-offset-2">
            justin20wjs@gmail.com
          </a>.
        </p>
      </Section>

      <Section title="2. There is no account">
        <p>
          MediSage has no registration, no login, and no user accounts. We do not ask for your
          email address, name, date of birth, or any other identifier, and there is no field
          anywhere in the product in which to supply one.
        </p>
      </Section>

      <Section title="3. What you send us">
        <p><strong className="text-foreground">Symptom text</strong> — the description you write to start an assessment.</p>
        <p><strong className="text-foreground">Follow-up answers</strong> — the yes / no / not sure answers you give to the questions that follow.</p>
        <p>
          That is the whole of it. Because this text is processed by a third-party AI provider
          (see section 4), do not include your name, identification numbers, addresses, or
          contact details in it.
        </p>
      </Section>

      <Section title="4. Where that text goes">
        <p>
          To produce a differential, your symptom text and answers are sent to a third-party
          AI provider — currently <strong className="text-foreground">Groq</strong> — which runs
          the language model that generates the output.
        </p>
        <p>
          Once that text reaches the provider, what they do with it is governed by{' '}
          <strong className="text-foreground">their</strong> policies, not ours. We do not control
          how long they hold it, whether they log it, or what they use it for, and we are not in a
          position to promise you otherwise. If that matters to you, read their terms before
          describing anything you would not want handled by a third party.
        </p>
      </Section>

      <Section title="5. What we keep: nothing">
        <p>
          We operate no database and no user storage. While an assessment is open, its state is
          held in the server's memory so that your answers can be applied to the differential
          you already have. That memory is not written to disk, not backed up, and not exported.
        </p>
        <p>
          It is discarded when the server restarts, which means an assessment left open long
          enough will simply stop being found. Nothing survives it.
        </p>
      </Section>

      <Section title="6. Your report is your copy">
        <p>
          At the end of an assessment you can download the result as a PDF or Word file. That
          download is generated on request and streamed straight to you — no copy is filed on
          our side.
        </p>
        <p>
          The file you save is therefore the only copy that exists, and it lives on your device
          under your control. Keeping it, sharing it, and deleting it are yours to decide.
        </p>
      </Section>

      <Section title="7. Cookies and tracking">
        <p>
          MediSage sets no cookies. There is no session to keep you signed in to, no advertising
          or cross-site tracking, and no analytics profile built from your visit.
        </p>
      </Section>

      <Section title="8. Requests about your data">
        <p>
          Rights of access, correction, and deletion apply to data an organisation holds about
          an identifiable person. We hold none: there is no account to close and no record to
          retrieve, because nothing is kept and nothing is linked to you.
        </p>
        <p>
          If you sent something you regret to the AI provider in section 4, that request has to
          be directed to them — we cannot reach into their systems on your behalf. You are
          welcome to write to us and we will tell you what we can.
        </p>
      </Section>

      <Section title="9. Not medical advice">
        <p>
          MediSage is an educational tool and is not a certified medical device. Its output
          is not a medical diagnosis and must not be relied upon as a substitute for
          professional medical advice, diagnosis, or treatment. If you believe you are
          experiencing a medical emergency, contact your local emergency services immediately.
        </p>
      </Section>

      <Section title="10. Changes to this policy">
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
