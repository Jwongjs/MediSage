# SP4 — UI/UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the MediSage frontend from styled-components to Tailwind CSS + shadcn/ui and deliver a production-grade light clinical redesign across all pages.

**Architecture:** All visual changes only — hooks, services, contexts, and types are untouched. Every view and component is rewritten using Tailwind utility classes + shadcn/ui primitives. The existing WorkflowRouter stage handling is preserved; only the rendered UI changes. SP3 stages (`awaiting_sign_responses`, `running_diagnosis`) receive placeholder routing now and will be fully implemented when SP3 is merged after SP4.

**Tech Stack:** React 18, TypeScript, Vite 5, Tailwind CSS v3, shadcn/ui (Default style, Slate base), Plus Jakarta Sans (via `@fontsource`), lucide-react, clsx + tailwind-merge, class-variance-authority, react-hook-form + zod

> **SP3 note:** SP3 is complete on branch `worktree-feature+sp3-diagnostic-workflow-refinement` but not yet merged into `feature/sp2-langgraph-rag`. SP4 runs on top of the SP2 state. `IntakeForm.tsx` and `SignCheckPanel.tsx` from SP3 will conflict with their Tailwind replacements created here — keep the Tailwind versions on merge.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `my-app/tsconfig.json` | Add `@/*` path alias required by shadcn/ui |
| Modify | `my-app/vite.config.ts` | Add `@` resolve alias |
| Create | `my-app/tailwind.config.ts` | Design tokens, clinical colour palette, custom animations |
| Create | `my-app/postcss.config.js` | PostCSS with Tailwind + Autoprefixer |
| Create | `my-app/components.json` | shadcn/ui project config |
| Create | `my-app/src/lib/utils.ts` | `cn()` helper (clsx + twMerge) |
| Create | `my-app/src/components/ui/` | shadcn/ui generated components (auto) |
| Replace | `my-app/src/index.css` | Tailwind directives + CSS variables (light clinical theme) |
| Delete | `my-app/src/App.css` | Replaced by Tailwind globals |
| Replace | `my-app/src/components/layout/Navbar.tsx` | Auth-aware navbar, mobile Sheet menu |
| Create | `my-app/src/components/layout/PageLayout.tsx` | Shared page wrapper with sticky Navbar |
| Create | `my-app/src/components/medical/DiagnosisProgress.tsx` | Multi-step progress indicator (6 stages) |
| Replace | `my-app/src/views/homepage.tsx` | Hero, features, how-it-works, CTA — all inline |
| Replace | `my-app/src/views/loginpage.tsx` | Centered Card login form |
| Replace | `my-app/src/views/registerpage.tsx` | Centered Card register form |
| Replace | `my-app/src/views/confirmationpage.tsx` | Email confirmation waiting screen |
| Replace | `my-app/src/views/diagnosis.tsx` | PageLayout wrapper, remove App.css import |
| Replace | `my-app/src/views/chatbot.tsx` | Full-height chat layout |
| Replace | `my-app/src/views/profilepage.tsx` | Avatar + Tabs (overview / sessions) |
| Modify | `my-app/src/WorkflowRouter.tsx` | Add SP3 stage placeholders; remove ImageAnalysisPage |
| Replace | `my-app/src/pages/diagnosis/DiagnosisFormPage.tsx` | Symptom input + initial results card |
| Replace | `my-app/src/pages/diagnosis/AnalysisProgressPage.tsx` | Processing indicator |
| Replace | `my-app/src/pages/diagnosis/FollowUpQuestionsPage.tsx` | Numbered Q&A form |
| Replace | `my-app/src/pages/diagnosis/FinalReportPage.tsx` | Severity badge, reasoning, alternatives, inline report |
| Replace | `my-app/src/pages/diagnosis/ErrorPage.tsx` | Alert + reset button |
| Replace | `my-app/src/components/medical/ChatPanel.tsx` | Bubble chat UI with scroll-area |
| Delete | `my-app/src/components/homepage/` | All — replaced by Tailwind inline in views/homepage.tsx |
| Delete | `my-app/src/components/common/` | All — replaced by shadcn/ui primitives |
| Delete | `my-app/src/components/medical/ImageUploadForm.tsx` | Image upload removed (SP1 decision) |
| Delete | `my-app/src/components/medical/ImageAnalysisResults.tsx` | Image analysis removed (SP1) |
| Delete | `my-app/src/pages/diagnosis/ImageAnalysisPage.tsx` | Image analysis removed (SP1) |
| Delete | `my-app/src/pages/homepage/` | All — replaced by views/homepage.tsx |
| Modify | `my-app/package.json` | Remove styled-components; deps already added in Task 1 |
| Modify | `docs/subprojects.md` | Update SP3 + SP4 status |

---

## Task 1: Install Tailwind CSS + shadcn/ui

**Files:**
- Modify: `my-app/tsconfig.json`
- Modify: `my-app/vite.config.ts`
- Create: `my-app/tailwind.config.ts`
- Create: `my-app/postcss.config.js`
- Create: `my-app/components.json`
- Create: `my-app/src/lib/utils.ts`

- [ ] **Step 1: Install npm dependencies**

```bash
cd my-app
npm install -D tailwindcss@3 postcss autoprefixer tailwindcss-animate
npm install @fontsource/instrument-serif @fontsource/dm-sans clsx tailwind-merge class-variance-authority lucide-react
npm install react-hook-form @hookform/resolvers zod
```

- [ ] **Step 2: Create `my-app/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } },
        'accordion-up': { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } },
        'fade-in-up': { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'slide-in-left': { from: { opacity: '0', transform: 'translateX(-12px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        'slide-in-right': { from: { opacity: '0', transform: 'translateX(12px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in-up': 'fade-in-up 0.4s ease-out both',
        'slide-in-left': 'slide-in-left 0.2s ease-out both',
        'slide-in-right': 'slide-in-right 0.2s ease-out both',
      },
    },
  },
  plugins: [animate],
} satisfies Config
```

- [ ] **Step 3: Create `my-app/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 4: Update `my-app/tsconfig.json` — add `@/*` path alias**

Add `"@/*": ["./src/*"]` to `compilerOptions.paths`. Full updated paths block:

```json
"paths": {
  "@/*": ["./src/*"],
  "components/*": ["components/*"],
  "types/*": ["types/*"],
  "utils/*": ["utils/*"],
  "hooks/*": ["hooks/*"],
  "pages/*": ["pages/*"]
}
```

- [ ] **Step 5: Update `my-app/vite.config.ts` — add `@` resolve alias**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path';

export default defineConfig({
  plugins: [
    react({ include: /\.[jt]sx?$/ }),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: false,
  },
});
```

- [ ] **Step 6: Create `my-app/components.json` (shadcn/ui config)**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

- [ ] **Step 7: Create `my-app/src/lib/utils.ts`**

```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 8: Add shadcn/ui components**

```bash
cd my-app
npx shadcn@latest add button card input label select textarea badge alert dialog tabs progress avatar separator skeleton scroll-area sheet form tooltip --yes
```

If `--yes` does not suppress prompts, answer: Style → `Default`, Base color → `Slate`.

- [ ] **Step 9: Verify build passes**

```bash
cd my-app && npm run build
```

Expected: `✓ built in X.XXs` — zero errors.

- [ ] **Step 10: Commit**

```bash
cd my-app
git add package.json package-lock.json tsconfig.json vite.config.ts tailwind.config.ts postcss.config.js components.json src/lib/utils.ts src/components/ui/
git commit -m "feat(sp4): install Tailwind CSS v3 + shadcn/ui, configure @/ alias, add 18 UI primitives"
```

---

## Task 2: Design Tokens + Global Styles

**Files:**
- Replace: `my-app/src/index.css`
- Modify: `my-app/src/main.tsx`

Light clinical theme: white surfaces (#f8fafc bg), sky-blue primary, emerald accent, slate typography. Plus Jakarta Sans as the single typeface.

- [ ] **Step 1: Read `my-app/src/index.css` and `my-app/src/main.tsx`**

Note what is currently in each file before overwriting.

- [ ] **Step 2: Replace `my-app/src/index.css` entirely**

```css
@import '@fontsource/instrument-serif/400.css';
@import '@fontsource/instrument-serif/400-italic.css';
@import '@fontsource/dm-sans/400.css';
@import '@fontsource/dm-sans/500.css';
@import '@fontsource/dm-sans/600.css';
@import '@fontsource/dm-sans/700.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 210 40% 98%;
    --foreground: 222 47% 11%;

    --card: 0 0% 100%;
    --card-foreground: 222 47% 11%;

    --popover: 0 0% 100%;
    --popover-foreground: 222 47% 11%;

    --primary: 199 89% 40%;
    --primary-foreground: 0 0% 100%;

    --secondary: 210 40% 96%;
    --secondary-foreground: 222 47% 11%;

    --muted: 210 40% 96%;
    --muted-foreground: 215 16% 47%;

    --accent: 160 84% 39%;
    --accent-foreground: 0 0% 100%;

    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 100%;

    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring: 199 89% 40%;

    --radius: 0.625rem;
  }
}

@layer base {
  * {
    @apply border-border box-border;
  }
  body {
    @apply bg-background text-foreground font-sans antialiased;
  }
  h2, h3, h4, h5, h6 {
    @apply font-semibold tracking-tight;
  }
}

/* Severity badge utility classes used in FinalReportPage */
@layer utilities {
  .severity-mild     { @apply bg-emerald-50 text-emerald-800; }
  .severity-moderate { @apply bg-amber-50   text-amber-800; }
  .severity-severe   { @apply bg-red-50     text-red-800; }
  .severity-critical { @apply bg-rose-50    text-rose-800; }
}
```

- [ ] **Step 3: Update `my-app/src/main.tsx` — keep only `index.css` stylesheet import**

The final `main.tsx` must import `'./index.css'` and no other CSS files:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from 'contexts/AuthContext';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

Adjust to match the current file's exact non-CSS imports — only remove extra stylesheet imports.

- [ ] **Step 4: Remove `App.css` import from `my-app/src/views/diagnosis.tsx`**

Delete only this one line from `views/diagnosis.tsx`:
```tsx
import 'App.css';
```

Make no other changes to the file in this step.

- [ ] **Step 5: Verify build**

```bash
cd my-app && npm run build
```

Expected: zero errors.

- [ ] **Step 6: Commit**

```bash
git add my-app/src/index.css my-app/src/main.tsx my-app/src/views/diagnosis.tsx
git commit -m "feat(sp4): design tokens -- light clinical CSS vars, Plus Jakarta Sans, Tailwind base layer"
```

---

## Task 3: Shared Layout — Navbar + PageLayout

**Files:**
- Replace: `my-app/src/components/layout/Navbar.tsx`
- Create: `my-app/src/components/layout/PageLayout.tsx`

Sticky navbar, blurred background, auth-aware (Profile + Logout when logged in; Login + Get started when not), mobile hamburger Sheet.

- [ ] **Step 1: Read `my-app/src/contexts/AuthContext.tsx`**

Note the exact properties returned by `useAuth()` — particularly `loggedIn`, `logout`. Adjust the component below if names differ.

- [ ] **Step 2: Replace `my-app/src/components/layout/Navbar.tsx`**

```tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { Menu, Activity, LogOut, User, Stethoscope, MessageSquare } from 'lucide-react';

const NAV_LINKS = [
  { label: 'Diagnosis', href: '/diagnosis', icon: Stethoscope },
  { label: 'Chat',      href: '/chatbot',   icon: MessageSquare },
] as const;

export const Navbar: React.FC = () => {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 max-w-6xl items-center justify-between px-4">

        <Link to="/" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
          <Activity className="h-5 w-5 text-primary" />
          <span className="font-bold text-lg tracking-tight">MediSage</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ label, href }) => (
            <Link key={href} to={href}
              className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors">
              {label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-2">
          {loggedIn ? (
            <>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/profile"><User className="h-4 w-4 mr-1.5" />Profile</Link>
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-1.5" />Log out
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" asChild><Link to="/login">Log in</Link></Button>
              <Button size="sm" asChild><Link to="/register">Get started</Link></Button>
            </>
          )}
        </div>

        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" /><span className="sr-only">Open menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-72">
            <div className="flex items-center gap-2 mb-6">
              <Activity className="h-5 w-5 text-primary" />
              <span className="font-bold text-lg">MediSage</span>
            </div>
            <nav className="flex flex-col gap-1">
              {NAV_LINKS.map(({ label, href, icon: Icon }) => (
                <Link key={href} to={href} onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                  <Icon className="h-4 w-4 text-muted-foreground" />{label}
                </Link>
              ))}
              <Separator className="my-3" />
              {loggedIn ? (
                <>
                  <Link to="/profile" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                    <User className="h-4 w-4 text-muted-foreground" />Profile
                  </Link>
                  <button onClick={handleLogout}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors text-destructive w-full">
                    <LogOut className="h-4 w-4" />Log out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                    Log in
                  </Link>
                  <Link to="/register" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg justify-center mt-1">
                    Get started
                  </Link>
                </>
              )}
            </nav>
          </SheetContent>
        </Sheet>

      </div>
    </header>
  );
};

export default Navbar;
```

- [ ] **Step 3: Create `my-app/src/components/layout/PageLayout.tsx`**

```tsx
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
```

- [ ] **Step 4: TypeScript check on new layout files**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep -E "layout/Navbar|layout/PageLayout"
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add my-app/src/components/layout/Navbar.tsx my-app/src/components/layout/PageLayout.tsx
git commit -m "feat(sp4): Navbar + PageLayout -- sticky blur header, auth-aware, mobile Sheet"
```

---

## Task 4: Homepage Redesign

**Files:**
- Replace: `my-app/src/views/homepage.tsx`

All sections inlined in `views/homepage.tsx`. Pages in `src/pages/homepage/` and components in `src/components/homepage/` are deleted in Task 10.

- [ ] **Step 1: Read `my-app/src/views/homepage.tsx` in full**

Note all existing hooks (useAuth, useNavigate) and logic before replacing.

- [ ] **Step 2: Replace `my-app/src/views/homepage.tsx`**

```tsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Activity, Brain, FileText, MessageSquare, ShieldCheck, ChevronRight, Clock, ArrowRight, Stethoscope } from 'lucide-react';

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
  { n: '01', title: 'Complete intake',       body: 'Age, medications, allergies, history — collected once, passed to every stage.' },
  { n: '02', title: 'Describe symptoms',     body: 'Natural language. The AI validates and flags vague or unsafe descriptions.' },
  { n: '03', title: 'Check observable signs', body: 'LLM-generated sign prompts targeted to your differential, then 4 adaptive follow-up questions.' },
  { n: '04', title: 'Receive your report',   body: 'Downloadable medical report with diagnosis, reasoning, severity, and next steps.' },
] as const;

const Homepage: React.FC = () => {
  const { loggedIn } = useAuth();
  const navigate = useNavigate();
  const cta = loggedIn ? '/diagnosis' : '/register';

  return (
    <PageLayout>

      {/* Hero — dark navy section with diagonal clip and dot-grid texture */}
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
        {/* Radial sky glow */}
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
                <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 hover:text-white" asChild>
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

      {/* Features — overlap the diagonal cut with negative margin */}
      <section className="container mx-auto max-w-6xl px-4 -mt-12 relative z-10 pb-16">
        <h2 className="text-2xl md:text-3xl font-bold mb-2">Built for your health journey</h2>
        <p className="text-muted-foreground mb-10 max-w-lg">Three tools. One goal: understand your health before seeing a doctor.</p>
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
          <p className="text-muted-foreground max-w-md">Create a free account and run your first diagnostic assessment in under two minutes.</p>
          <Button size="lg" onClick={() => navigate(cta)} className="gap-2 mt-2">
            {loggedIn ? 'Go to diagnosis' : 'Create free account'}<ArrowRight className="h-4 w-4" />
          </Button>
          <p className="text-xs text-muted-foreground">For educational purposes only. Not a substitute for professional medical advice.</p>
        </div>
      </section>

    </PageLayout>
  );
};

export default Homepage;
```

- [ ] **Step 3: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep "views/homepage"
```

Expected: 0 errors.

- [ ] **Step 4: Visual smoke test — start dev server**

```bash
cd my-app && npm run dev
```

Open http://localhost:3000. Confirm: Navbar renders, hero grid background visible, three feature cards, four-step grid, CTA section, no console errors.

- [ ] **Step 5: Commit**

```bash
git add my-app/src/views/homepage.tsx
git commit -m "feat(sp4): homepage -- hero with grid bg, feature cards, how-it-works, CTA"
```

---

## Task 5: Auth Pages — Login, Register, Confirmation

**Files:**
- Replace: `my-app/src/views/loginpage.tsx`
- Replace: `my-app/src/views/registerpage.tsx`
- Replace: `my-app/src/views/confirmationpage.tsx`

- [ ] **Step 1: Read all three current files**

Note: the exact method names from `useAuth()` (likely `login`) and from `AuthService` (likely `AuthService.signUp`). Update Steps 2–3 if names differ.

- [ ] **Step 2: Replace `my-app/src/views/loginpage.tsx`**

```tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Activity, AlertCircle, Loader2 } from 'lucide-react';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message ?? 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout className="flex items-center justify-center py-16 px-4">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">MediSage</span>
          </div>
        </div>
        <Card className="shadow-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">Welcome back</CardTitle>
            <CardDescription>Sign in to continue to your account</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email address</Label>
                <Input id="email" type="email" placeholder="you@example.com" autoComplete="email"
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" placeholder="••••••••" autoComplete="current-password"
                  value={password} onChange={e => setPassword(e.target.value)} required />
              </div>
            </CardContent>
            <CardFooter className="flex-col gap-4 pt-2">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Signing in…</> : 'Sign in'}
              </Button>
              <p className="text-sm text-muted-foreground text-center">
                No account?{' '}
                <Link to="/register" className="text-primary hover:underline font-medium">Create one for free</Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </PageLayout>
  );
};

export default Login;
```

- [ ] **Step 3: Replace `my-app/src/views/registerpage.tsx`**

```tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthService } from 'services/auth';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Activity, AlertCircle, Loader2 } from 'lucide-react';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    if (password.length < 8)  { setError('Password must be at least 8 characters.'); return; }
    setError(null);
    setLoading(true);
    try {
      await AuthService.signUp(email, password);
      navigate('/confirmation-pending');
    } catch (err: any) {
      setError(err.message ?? 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout className="flex items-center justify-center py-16 px-4">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">MediSage</span>
          </div>
        </div>
        <Card className="shadow-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">Create your account</CardTitle>
            <CardDescription>Free to use. No personal health data required.</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="reg-email">Email address</Label>
                <Input id="reg-email" type="email" placeholder="you@example.com" autoComplete="email"
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reg-password">Password</Label>
                <Input id="reg-password" type="password" placeholder="At least 8 characters" autoComplete="new-password"
                  value={password} onChange={e => setPassword(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reg-confirm">Confirm password</Label>
                <Input id="reg-confirm" type="password" placeholder="Repeat your password" autoComplete="new-password"
                  value={confirm} onChange={e => setConfirm(e.target.value)} required />
              </div>
            </CardContent>
            <CardFooter className="flex-col gap-4 pt-2">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Creating account…</> : 'Create account'}
              </Button>
              <p className="text-sm text-muted-foreground text-center">
                Already have an account?{' '}
                <Link to="/login" className="text-primary hover:underline font-medium">Sign in</Link>
              </p>
              <p className="text-xs text-muted-foreground text-center">
                Do not enter real personal health information. Data is processed by Groq and stored on Supabase.
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </PageLayout>
  );
};

export default Register;
```

- [ ] **Step 4: Replace `my-app/src/views/confirmationpage.tsx`**

```tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Mail } from 'lucide-react';

const ConfirmationPending: React.FC = () => (
  <PageLayout className="flex items-center justify-center py-16 px-4">
    <div className="w-full max-w-sm animate-fade-in">
      <div className="flex justify-center mb-6">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-primary" />
          <span className="font-bold text-xl">MediSage</span>
        </div>
      </div>
      <Card className="shadow-sm text-center">
        <CardHeader className="pb-3">
          <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-xl">Check your inbox</CardTitle>
          <CardDescription>
            We sent a confirmation link to your email. Click it to activate your account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Didn't receive it? Check your spam folder. The link expires in 24 hours.
          </p>
          <Button variant="outline" className="w-full" asChild>
            <Link to="/login">Back to sign in</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  </PageLayout>
);

export default ConfirmationPending;
```

- [ ] **Step 5: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep -E "loginpage|registerpage|confirmationpage"
```

Expected: 0 errors. If `AuthService.signUp` is not the correct method name, check `src/services/auth.ts` and update accordingly.

- [ ] **Step 6: Commit**

```bash
git add my-app/src/views/loginpage.tsx my-app/src/views/registerpage.tsx my-app/src/views/confirmationpage.tsx
git commit -m "feat(sp4): auth pages -- Login, Register, ConfirmationPending with shadcn Card + Alert"
```

---

## Task 6: Diagnosis Flow — Progress Indicator + Form Stage

**Files:**
- Create: `my-app/src/components/medical/DiagnosisProgress.tsx`
- Replace: `my-app/src/pages/diagnosis/DiagnosisFormPage.tsx`
- Replace: `my-app/src/pages/diagnosis/ErrorPage.tsx`
- Modify: `my-app/src/views/diagnosis.tsx`
- Modify: `my-app/src/WorkflowRouter.tsx`

- [ ] **Step 1: Read `my-app/src/pages/diagnosis/DiagnosisFormPage.tsx` and `my-app/src/hooks/useDiagnosis.ts`**

Confirm the exact `DiagnosisFormPageProps` interface. The replacement preserves: `onSubmit`, `onContinue`, `loading`, `sessionId`, `workflowState`, `workflowInfo`.

- [ ] **Step 2: Create `my-app/src/components/medical/DiagnosisProgress.tsx`**

```tsx
import React from 'react';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

export type DiagnosisStage = 'intake' | 'symptoms' | 'analysis' | 'signs' | 'followup' | 'report';

const STAGES: { id: DiagnosisStage; label: string }[] = [
  { id: 'intake',   label: 'Intake'    },
  { id: 'symptoms', label: 'Symptoms'  },
  { id: 'analysis', label: 'Analysis'  },
  { id: 'signs',    label: 'Signs'     },
  { id: 'followup', label: 'Follow-up' },
  { id: 'report',   label: 'Report'    },
];

interface DiagnosisProgressProps {
  current: DiagnosisStage;
}

export const DiagnosisProgress: React.FC<DiagnosisProgressProps> = ({ current }) => {
  const ci = STAGES.findIndex(s => s.id === current);

  return (
    <nav aria-label="Diagnosis progress">
      <ol className="flex items-center">
        {STAGES.map(({ id, label }, i) => {
          const done   = i < ci;
          const active = i === ci;
          return (
            <li key={id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1">
                <div className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-all',
                  done   && 'bg-accent text-accent-foreground',
                  active && 'bg-primary text-primary-foreground ring-4 ring-primary/20',
                  !done && !active && 'bg-secondary text-muted-foreground',
                )}>
                  {done ? <Check className="h-3.5 w-3.5" /> : <span>{i + 1}</span>}
                </div>
                <span className={cn(
                  'text-[10px] sm:text-xs font-medium hidden sm:block',
                  active ? 'text-primary' : done ? 'text-accent' : 'text-muted-foreground',
                )}>
                  {label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div className={cn('h-px flex-1 -mt-4 mx-1 transition-colors', i < ci ? 'bg-accent' : 'bg-border')} />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
```

- [ ] **Step 3: Replace `my-app/src/pages/diagnosis/DiagnosisFormPage.tsx`**

```tsx
import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Stethoscope, ChevronRight } from 'lucide-react';

interface DiagnosisFormPageProps {
  onSubmit: (symptoms: string) => Promise<void>;
  onContinue: () => void;
  loading: boolean;
  sessionId: string | null;
  workflowState: AgentState | null;
  workflowInfo?: any | null;
}

export const DiagnosisFormPage: React.FC<DiagnosisFormPageProps> = ({
  onSubmit, onContinue, loading, workflowState,
}) => {
  const [symptoms, setSymptoms] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);

  const hasDiagnosis = (workflowState?.textual_analysis ?? []).length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symptoms.trim().split(/\s+/).length < 5) {
      setInputError('Please describe your symptoms in more detail (at least a few words).');
      return;
    }
    setInputError(null);
    await onSubmit(symptoms);
  };

  if (!hasDiagnosis) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="symptoms" />
        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2 mb-1">
              <Stethoscope className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">Describe your symptoms</CardTitle>
            </div>
            <CardDescription>
              Include location, onset, severity, duration, and associated symptoms.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {inputError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{inputError}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="symptoms">Your symptoms</Label>
                <Textarea id="symptoms"
                  placeholder="e.g. Persistent headache on the right side for 3 days with nausea and light sensitivity…"
                  className="min-h-[120px] resize-none"
                  value={symptoms} onChange={e => setSymptoms(e.target.value)}
                  disabled={loading} required />
              </div>
              <p className="text-xs text-muted-foreground">
                Do not include personally identifying information such as your name or ID number.
              </p>
              <Button type="submit" className="w-full" disabled={loading || !symptoms.trim()}>
                {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analysing…</> : 'Start diagnosis'}
              </Button>
            </CardContent>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="symptoms" />
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Initial assessment complete</CardTitle>
          <CardDescription>Preliminary differential generated. Continue to check observable signs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {(workflowState!.textual_analysis ?? []).slice(0, 3).map((d, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-sm font-medium">{d.text_diagnosis}</span>
                <Badge variant={i === 0 ? 'default' : 'secondary'} className="text-xs shrink-0">
                  {Math.round(d.diagnosis_confidence * 100)}%
                </Badge>
              </div>
            ))}
          </div>
          <Button onClick={onContinue} className="w-full gap-2" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><ChevronRight className="h-4 w-4" />Continue to sign check</>}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
```

- [ ] **Step 4: Replace `my-app/src/pages/diagnosis/ErrorPage.tsx`**

```tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface ErrorPageProps {
  error: string;
  onReset: () => void;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({ error, onReset }) => (
  <div className="max-w-md mx-auto space-y-4 py-8">
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
    </Alert>
    <Button variant="outline" onClick={onReset} className="gap-2">
      <RotateCcw className="h-4 w-4" />Start over
    </Button>
  </div>
);
```

- [ ] **Step 5: Update `my-app/src/views/diagnosis.tsx` — wrap with PageLayout**

Read the current file. Add `PageLayout` import and wrap the returned JSX. Only add the wrapper — do NOT touch hooks, handlers, or prop passing.

Add import:
```tsx
import { PageLayout } from 'components/layout/PageLayout';
```

Wrap the return:
```tsx
return (
  <PageLayout>
    <div className="container mx-auto max-w-3xl px-4 py-8">
      {/* existing JSX unchanged */}
    </div>
  </PageLayout>
);
```

- [ ] **Step 6: Update `my-app/src/WorkflowRouter.tsx` — three surgical changes**

Read the current file first.

**Change 1** — Remove the `ImageAnalysisPage` import line.

**Change 2** — Remove the entire `case 'awaiting_image_upload': case 'analyzing_image': case 'image_analysis_complete':` block.

**Change 3** — After the `'textual_analysis_complete'` case, add:

```tsx
    // SP3 stages — complete after SP3 merge
    case 'initializing':
    case 'running_diagnosis':
      return (
        <AnalysisProgressPage
          workflowState={workflowState}
          loading={loading}
          onReset={onReset}
          onContinue={onContinue}
        />
      );
    case 'awaiting_sign_responses':
      return (
        <DiagnosisFormPage
          onSubmit={onStartDiagnosis}
          onContinue={onContinue}
          loading={loading}
          sessionId={sessionId}
          workflowState={workflowState}
          workflowInfo={workflowInfo}
        />
      );
```

- [ ] **Step 7: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep -E "DiagnosisFormPage|DiagnosisProgress|WorkflowRouter|views/diagnosis"
```

Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add my-app/src/components/medical/DiagnosisProgress.tsx my-app/src/pages/diagnosis/DiagnosisFormPage.tsx my-app/src/pages/diagnosis/ErrorPage.tsx my-app/src/views/diagnosis.tsx my-app/src/WorkflowRouter.tsx
git commit -m "feat(sp4): diagnosis form stage -- DiagnosisProgress stepper, DiagnosisFormPage, ErrorPage; SP3 placeholders"
```

---

## Task 7: Diagnosis Flow — Analysis Progress, Follow-Up + Report

**Files:**
- Replace: `my-app/src/pages/diagnosis/AnalysisProgressPage.tsx`
- Replace: `my-app/src/pages/diagnosis/FollowUpQuestionsPage.tsx`
- Replace: `my-app/src/pages/diagnosis/FinalReportPage.tsx`

- [ ] **Step 1: Read all three current files in full**

Note exact prop interfaces and which `workflowState` fields each accesses (`overall_analysis`, `followup_questions`, `followup_diagnosis`, `medical_report`, `textual_analysis`). Adjust field names below if they differ from those in `types/medical.ts`.

- [ ] **Step 2: Replace `my-app/src/pages/diagnosis/AnalysisProgressPage.tsx`**

```tsx
import React from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, ChevronRight, Brain } from 'lucide-react';

interface AnalysisProgressPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
  onContinue: () => void;
}

export const AnalysisProgressPage: React.FC<AnalysisProgressPageProps> = ({
  workflowState, loading, onContinue,
}) => {
  const isProcessing = loading || workflowState?.current_workflow_stage === 'performing_overall_analysis';

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="analysis" />
      <Card className="shadow-sm text-center">
        <CardHeader>
          <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-2">
            {isProcessing
              ? <Loader2 className="h-7 w-7 text-primary animate-spin" />
              : <Brain className="h-7 w-7 text-primary" />}
          </div>
          <CardTitle className="text-lg">
            {isProcessing ? 'Analysing your responses…' : 'Analysis complete'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
            {isProcessing
              ? 'The AI is integrating your symptoms, signs, and follow-up answers. This usually takes a few seconds.'
              : 'All data processed. Continue to generate your medical report.'}
          </p>
          {!isProcessing && (
            <Button onClick={onContinue} className="gap-2">
              <ChevronRight className="h-4 w-4" />Continue to report
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
```

- [ ] **Step 3: Replace `my-app/src/pages/diagnosis/FollowUpQuestionsPage.tsx`**

```tsx
import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, ChevronRight, MessageSquare } from 'lucide-react';

interface FollowUpQuestionsPageProps {
  workflowState: AgentState | null;
  workflowInfo?: any | null;
  loading: boolean;
  onSubmitResponses: (responses: Record<string, string>) => Promise<void>;
  onContinue: () => void;
  onReset: () => void;
}

export const FollowUpQuestionsPage: React.FC<FollowUpQuestionsPageProps> = ({
  workflowState, loading, onSubmitResponses, onContinue,
}) => {
  const questions   = workflowState?.followup_questions ?? [];
  const hasResponses = (workflowState?.followup_diagnosis ?? []).length > 0;
  const [responses, setResponses] = useState<Record<string, string>>({});

  const allAnswered = questions.length > 0 && questions.every(q => (responses[q] ?? '').trim().length > 0);

  if (hasResponses) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="followup" />
        <Card className="shadow-sm text-center">
          <CardHeader>
            <CardTitle className="text-lg">Follow-up complete</CardTitle>
            <CardDescription>Responses analysed. Continue to overall analysis.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={onContinue} className="gap-2" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><ChevronRight className="h-4 w-4" />Continue to analysis</>}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DiagnosisProgress current="followup" />
      <Card className="shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2 mb-1">
            <MessageSquare className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Follow-up questions</CardTitle>
          </div>
          <CardDescription>Answer accurately — these are tailored to your symptom profile.</CardDescription>
        </CardHeader>
        <form onSubmit={async e => { e.preventDefault(); await onSubmitResponses(responses); }}>
          <CardContent className="space-y-5">
            {questions.map((q, i) => (
              <div key={i} className="space-y-1.5">
                <Label htmlFor={`q-${i}`} className="text-sm leading-relaxed">
                  <span className="text-muted-foreground font-mono mr-1.5">{i + 1}.</span>{q}
                </Label>
                <Textarea id={`q-${i}`} placeholder="Your answer…" className="min-h-[80px] resize-none text-sm"
                  value={responses[q] ?? ''} onChange={e => setResponses(p => ({ ...p, [q]: e.target.value }))}
                  disabled={loading} />
              </div>
            ))}
            <Button type="submit" className="w-full" disabled={loading || !allAnswered}>
              {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting…</> : 'Submit answers'}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
};
```

- [ ] **Step 4: Replace `my-app/src/pages/diagnosis/FinalReportPage.tsx`**

Read the current file to confirm: (a) the prop interface, (b) any PDF/DOCX download handlers. Preserve download handlers — wrap them in the new layout.

```tsx
import React, { useState } from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisProgress } from 'components/medical/DiagnosisProgress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, FileText, RotateCcw, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FinalReportPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
}

const SEVERITY_CLASS: Record<string, string> = {
  mild:     'severity-mild',
  moderate: 'severity-moderate',
  severe:   'severity-severe',
  critical: 'severity-critical',
  emergency:'severity-critical',
};

export const FinalReportPage: React.FC<FinalReportPageProps> = ({
  workflowState, loading, onReset,
}) => {
  const [reportOpen, setReportOpen] = useState(false);

  if (loading || !workflowState?.overall_analysis) {
    return (
      <div className="space-y-6">
        <DiagnosisProgress current="report" />
        <Card className="shadow-sm text-center">
          <CardContent className="py-12 space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-sm text-muted-foreground">Generating your medical report…</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const analysis   = workflowState.overall_analysis;
  const severity   = (analysis.final_severity ?? 'mild').toLowerCase();
  const isCritical = severity === 'critical' || severity === 'emergency';
  const alts = (workflowState.followup_diagnosis?.length ?? 0) > 1
    ? workflowState.followup_diagnosis!.slice(1, 4)
    : (workflowState.textual_analysis ?? []).slice(1, 4);

  return (
    <div className="space-y-6 animate-fade-in">
      <DiagnosisProgress current="report" />

      {isCritical && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Emergency — seek immediate care</AlertTitle>
          <AlertDescription>
            One or more symptoms may indicate a life-threatening condition. Call 911 or go to the nearest emergency room immediately.
          </AlertDescription>
        </Alert>
      )}

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <CardDescription className="text-xs mb-1">Primary diagnosis</CardDescription>
              <CardTitle className="text-xl">{analysis.final_diagnosis}</CardTitle>
            </div>
            <Badge className={cn('text-xs', SEVERITY_CLASS[severity] ?? SEVERITY_CLASS.mild)}>
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {analysis.user_explanation && (
            <div className="bg-secondary/60 rounded-lg p-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">What this means</p>
              <p className="text-sm leading-relaxed">{analysis.user_explanation}</p>
            </div>
          )}
          {analysis.clinical_reasoning && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">Clinical reasoning</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{analysis.clinical_reasoning}</p>
            </div>
          )}
          {analysis.specialist_recommendation && (
            <>
              <Separator />
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Recommended specialist</p>
                <Badge variant="outline" className="text-xs">{analysis.specialist_recommendation}</Badge>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {alts.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Alternative diagnoses considered</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alts.map((d, i) => {
              const pct = Math.round(d.diagnosis_confidence * 100);
              return (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{d.text_diagnosis}</span>
                    <span className="text-muted-foreground text-xs">{pct}%</span>
                  </div>
                  <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-primary/50 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        {workflowState.medical_report && (
          <Button variant="outline" className="gap-2 flex-1" onClick={() => setReportOpen(r => !r)}>
            <FileText className="h-4 w-4" />{reportOpen ? 'Hide' : 'View'} full report
          </Button>
        )}
        <Button variant="outline" onClick={onReset} className="gap-2 flex-1">
          <RotateCcw className="h-4 w-4" />New diagnosis
        </Button>
      </div>

      {reportOpen && workflowState.medical_report && (
        <Card className="shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Full Medical Report</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96 w-full rounded border bg-secondary/30">
              <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed p-4">
                {workflowState.medical_report}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-center text-muted-foreground">
        AI-generated for informational purposes only. Not a medical diagnosis. Always consult a qualified healthcare professional.
      </p>
    </div>
  );
};
```

- [ ] **Step 5: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep -E "AnalysisProgress|FollowUp|FinalReport"
```

Expected: 0 errors. If `overall_analysis` field names differ, check `types/medical.ts` and adjust.

- [ ] **Step 6: Commit**

```bash
git add my-app/src/pages/diagnosis/
git commit -m "feat(sp4): diagnosis results -- AnalysisProgress, FollowUp, FinalReport with severity + alternatives"
```

---

## Task 8: Chatbot Page

**Files:**
- Replace: `my-app/src/components/medical/ChatPanel.tsx`
- Replace: `my-app/src/views/chatbot.tsx`

- [ ] **Step 1: Read `my-app/src/components/medical/ChatPanel.tsx` and `my-app/src/hooks/useChat.ts`**

Note the exact return shape of `useChat()`. The replacement assumes `{ messages, sendMessage, loading, input, setInput }`. If `input`/`setInput` are not returned by the hook, manage input state locally (add `const [input, setInput] = useState('')` inside the component and call `setInput('')` after `sendMessage`).

- [ ] **Step 2: Replace `my-app/src/components/medical/ChatPanel.tsx`**

```tsx
import React, { useRef, useEffect } from 'react';
import { useChat } from 'hooks/useChat';
import { useAuth } from 'contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Send, Loader2, Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ChatPanel: React.FC = () => {
  const { messages, sendMessage, loading, input, setInput } = useChat();
  const { loggedIn } = useAuth();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    await sendMessage(input.trim());
  };

  return (
    <div className="flex flex-col h-full border rounded-xl overflow-hidden bg-card shadow-sm">
      <div className="flex items-center gap-2.5 px-4 py-3 border-b bg-secondary/30 shrink-0">
        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-tight">MediSage Assistant</p>
          <p className="text-xs text-muted-foreground truncate">Answers questions about your health history</p>
        </div>
        <Badge variant="outline" className="ml-auto text-xs shrink-0">Beta</Badge>
      </div>

      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[200px] gap-2 text-center py-12">
            <Bot className="h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">Ask me about your past diagnostic sessions or health history.</p>
            <p className="text-xs text-muted-foreground/60">I can only answer based on information from your saved reports.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user';
              return (
                <div key={i} className={cn('flex items-end gap-2', isUser && 'flex-row-reverse')}>
                  <div className={cn('w-6 h-6 rounded-full flex items-center justify-center shrink-0',
                    isUser ? 'bg-primary/10' : 'bg-secondary')}>
                    {isUser ? <User className="h-3.5 w-3.5 text-primary" /> : <Bot className="h-3.5 w-3.5 text-muted-foreground" />}
                  </div>
                  <div className={cn(
                    'max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                    isUser
                      ? 'bg-primary text-primary-foreground rounded-br-sm animate-slide-in-right'
                      : 'bg-secondary text-foreground rounded-bl-sm animate-slide-in-left',
                  )}>
                    {msg.content}
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="flex items-end gap-2">
                <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center shrink-0">
                  <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div className="bg-secondary rounded-2xl rounded-bl-sm px-3.5 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      <Separator />

      <form onSubmit={handleSend} className="flex items-center gap-2 px-3 py-2.5 shrink-0">
        {loggedIn ? (
          <>
            <Input value={input} onChange={e => setInput(e.target.value)}
              placeholder="Ask about your health history…"
              className="flex-1 border-0 focus-visible:ring-0 bg-transparent text-sm" disabled={loading} />
            <Button type="submit" size="icon" variant="ghost" disabled={loading || !input.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4 text-primary" />}
            </Button>
          </>
        ) : (
          <p className="text-xs text-muted-foreground py-1 w-full text-center">Sign in to use the chat assistant</p>
        )}
      </form>
    </div>
  );
};
```

- [ ] **Step 3: Replace `my-app/src/views/chatbot.tsx`**

```tsx
import React from 'react';
import { PageLayout } from 'components/layout/PageLayout';
import { ChatPanel } from 'components/medical/ChatPanel';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck } from 'lucide-react';

const ChatbotPage: React.FC = () => (
  <PageLayout>
    <div className="container mx-auto max-w-3xl px-4 py-8 flex flex-col" style={{ height: 'calc(100vh - 3.5rem)' }}>
      <div className="mb-4 shrink-0">
        <h1 className="text-xl font-bold">Health Assistant</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Powered by your diagnostic history and uploaded medical reports.
        </p>
      </div>
      <div className="mb-4 shrink-0">
        <Badge variant="outline" className="text-xs gap-1.5">
          <ShieldCheck className="h-3 w-3 text-accent" />Answers from your records only
        </Badge>
      </div>
      <div className="flex-1 min-h-0">
        <ChatPanel />
      </div>
      <p className="text-xs text-center text-muted-foreground mt-3 shrink-0">
        This assistant cannot diagnose new symptoms. Use the{' '}
        <a href="/diagnosis" className="text-primary hover:underline">Diagnosis</a> tool for new assessments.
      </p>
    </div>
  </PageLayout>
);

export default ChatbotPage;
```

- [ ] **Step 4: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep -E "chatbot|ChatPanel"
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add my-app/src/components/medical/ChatPanel.tsx my-app/src/views/chatbot.tsx
git commit -m "feat(sp4): chatbot -- message bubbles, scroll-area, bot/user avatars, full-height layout"
```

---

## Task 9: Profile Page

**Files:**
- Replace: `my-app/src/views/profilepage.tsx`

- [ ] **Step 1: Read `my-app/src/views/profilepage.tsx` in full**

Note all data fields displayed, all action handlers (logout, session fetch, etc.), and any Supabase data-fetching logic. If the current file fetches session history, preserve those calls and render the data inside `TabsContent value="sessions"`.

- [ ] **Step 2: Replace `my-app/src/views/profilepage.tsx`**

```tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LogOut, User, Activity, ShieldCheck } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const email    = (user as any)?.email ?? '';
  const initials = email.slice(0, 2).toUpperCase() || 'ME';

  return (
    <PageLayout>
      <div className="container mx-auto max-w-3xl px-4 py-10">

        <div className="flex items-center gap-4 mb-8 flex-wrap">
          <Avatar className="h-14 w-14 shrink-0">
            <AvatarFallback className="bg-primary/10 text-primary font-semibold text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <h1 className="text-xl font-bold truncate">{email || 'Your account'}</h1>
            <div className="flex items-center gap-1.5 mt-1">
              <ShieldCheck className="h-3.5 w-3.5 text-accent shrink-0" />
              <span className="text-xs text-muted-foreground">Account active</span>
            </div>
          </div>
          <Button variant="outline" size="sm" className="ml-auto gap-1.5 shrink-0" onClick={handleLogout}>
            <LogOut className="h-3.5 w-3.5" />Log out
          </Button>
        </div>

        <Tabs defaultValue="overview">
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="gap-1.5"><User className="h-3.5 w-3.5" />Overview</TabsTrigger>
            <TabsTrigger value="sessions" className="gap-1.5"><Activity className="h-3.5 w-3.5" />Sessions</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card className="shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="text-base">Account information</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Email</span>
                  <span className="text-sm font-medium">{email}</span>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Privacy policy</span>
                  <Badge variant="outline" className="text-xs gap-1">
                    <ShieldCheck className="h-3 w-3 text-accent" />Accepted
                  </Badge>
                </div>
              </CardContent>
            </Card>
            <Card className="shadow-sm border-destructive/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-destructive">Danger zone</CardTitle>
                <CardDescription>Irreversible account actions.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="destructive" size="sm" onClick={handleLogout}>Sign out of all sessions</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sessions">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Diagnostic sessions</CardTitle>
                <CardDescription>Your past MediSage assessments will appear here.</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Preserve any existing session-fetch logic and render it here */}
                <p className="text-sm text-muted-foreground text-center py-8">
                  No sessions recorded yet. Complete a diagnosis to see your history.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

      </div>
    </PageLayout>
  );
};

export default ProfilePage;
```

- [ ] **Step 3: TypeScript check**

```bash
cd my-app && npx tsc --noEmit 2>&1 | grep "profilepage"
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add my-app/src/views/profilepage.tsx
git commit -m "feat(sp4): profile page -- Avatar, Tabs (overview/sessions), account info card"
```

---

## Task 10: Cleanup — Remove styled-components + Dead Files

**Files:**
- Modify: `my-app/package.json`
- Delete: multiple (see steps)
- Modify: `docs/subprojects.md`

- [ ] **Step 1: Find all remaining styled-components usages**

```bash
cd my-app && grep -r "from 'styled-components'\|from \"styled-components\"" src/ --include="*.tsx" --include="*.ts" -l
```

For each file listed that was NOT replaced in Tasks 3–9, either rewrite it in Tailwind or delete it if it is dead code (nothing else imports it).

- [ ] **Step 2: Check for stale imports to the old component directories**

```bash
cd my-app && grep -r "from 'components/homepage/" src/ --include="*.tsx" -l
```

Update any remaining imports: `components/homepage/Navbar` → `components/layout/Navbar`.

```bash
cd my-app && grep -r "ImageAnalysisPage\|ImageUpload\|ImageAnalysis" src/ --include="*.tsx" -l
```

Expected: empty (WorkflowRouter was cleaned in Task 6).

- [ ] **Step 3: Handle `PrivacyPolicyModal` — check if still imported**

```bash
cd my-app && grep -r "PrivacyPolicyModal" src/ --include="*.tsx" -l
```

If `views/diagnosis.tsx` still imports it, open `src/components/medical/PrivacyPolicyModal.tsx`, read it, and replace its styled-components markup with an equivalent shadcn `Dialog`:

```tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
// Replace styled-components wrapper with Dialog component, preserving existing props and logic
```

- [ ] **Step 4: Delete dead file trees**

Run in PowerShell from the repo root:

```powershell
Remove-Item -Recurse -Force my-app/src/components/homepage
Remove-Item -Recurse -Force my-app/src/components/common
Remove-Item -Force my-app/src/components/medical/ImageUploadForm.tsx -ErrorAction SilentlyContinue
Remove-Item -Force my-app/src/components/medical/ImageAnalysisResults.tsx -ErrorAction SilentlyContinue
Remove-Item -Force my-app/src/pages/diagnosis/ImageAnalysisPage.tsx -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force my-app/src/pages/homepage
Remove-Item -Force my-app/src/App.css -ErrorAction SilentlyContinue
```

Check if `MedicalReportModal.tsx` is still imported anywhere:
```bash
cd my-app && grep -r "MedicalReportModal" src/ --include="*.tsx" -l
```
If nothing imports it, delete it:
```powershell
Remove-Item -Force my-app/src/components/medical/MedicalReportModal.tsx
```

- [ ] **Step 5: Uninstall styled-components**

```bash
cd my-app && npm uninstall styled-components @types/styled-components
```

- [ ] **Step 6: Full TypeScript check — must reach zero errors**

```bash
cd my-app && npx tsc --noEmit
```

Expected: 0 errors. Common fixes:
- Deleted file still imported somewhere → find with `grep` and remove the import.
- A shadcn/ui component used but not generated → `npx shadcn@latest add <name>`.
- `useChat` hook shape mismatch → adjust ChatPanel per Task 8 Step 1 note.

- [ ] **Step 7: Production build — clean pass**

```bash
cd my-app && npm run build
```

Expected: `✓ built in X.XXs` — no styled-components warnings, no missing file errors.

- [ ] **Step 8: Update `docs/subprojects.md` status tracker**

Replace the SP3 and SP4 rows:

```markdown
| SP3 | ✅ Complete (pending merge) | — | Linear 6-node graph, intake form, sign prompts, prompt guard. Branch: `worktree-feature+sp3-diagnostic-workflow-refinement`. Merge deferred until after SP4. |
| SP4 | ✅ Complete | SP1, SP3 | CRA→Vite done (SP4a). Tailwind + shadcn/ui. Plus Jakarta Sans. Light clinical theme. All pages redesigned. SP3 UI stages use placeholders — finalize on SP3 merge. |
```

- [ ] **Step 9: Final commit**

```bash
git add -A
git commit -m "feat(sp4): cleanup -- remove styled-components, dead files (homepage cmps, common, image analysis); 0 TS errors, build clean"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task |
|---|---|
| CRA → Vite | Done in SP4a pre-work |
| Tailwind CSS v3 install + config | 1 |
| shadcn/ui component library (18 components) | 1 |
| Plus Jakarta Sans typography | 1, 2 |
| Light clinical design tokens (CSS vars) | 2 |
| Shared sticky Navbar — auth-aware, mobile | 3 |
| PageLayout shared wrapper | 3 |
| Homepage redesign (hero, features, how-it-works, CTA) | 4 |
| Login page | 5 |
| Register page | 5 |
| Privacy policy gate frontend (confirmation screen) | 5 |
| Diagnosis — 6-step progress indicator | 6 |
| Diagnosis — symptom form stage | 6 |
| Diagnosis — SP3 stage placeholders in WorkflowRouter | 6 |
| Diagnosis — analysis loading | 7 |
| Diagnosis — follow-up questions | 7 |
| Diagnosis — final report with severity badges + alternatives | 7 |
| Chatbot page | 8 |
| Profile page with Tabs | 9 |
| Remove styled-components | 10 |
| Remove image analysis dead code (SP1 decision) | 10 |
| TypeScript clean (0 errors) | Each task + 10 |
| Production build passes | 10 |
| `docs/subprojects.md` updated | 10 |

**Gaps addressed in-plan:**
- `PrivacyPolicyModal` — still uses styled-components after Tasks 3–9; Task 10 Step 3 explicitly migrates it to shadcn `Dialog`.
- `MedicalReportModal` — replaced by inline toggle in `FinalReportPage`; Task 10 Step 4 checks for orphaned import and deletes.
- `ProfileDropdown.tsx` — lives in `components/homepage/` deleted in Task 10 Step 4; no other file imports it after Navbar is replaced in Task 3.
- `useChat` shape — Task 8 Step 1 reads the hook before writing; Step 4 has fallback instructions for missing `input`/`setInput`.
- Session history in ProfilePage — Task 9 Step 1 reads the current file and Step 2 comments preserve the fetch logic slot.
