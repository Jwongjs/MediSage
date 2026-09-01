create table if not exists diagnosis_sessions (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  session_id     text not null,
  title          text,
  patient_text   text not null,
  steps          jsonb not null default '[]'::jsonb,
  final_ranking  jsonb,
  not_evaluated  jsonb not null default '[]'::jsonb,
  canonical      jsonb,
  matrix         jsonb,
  judgements     jsonb,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  -- One row per session: finalize is idempotent, not append-only.
  unique (user_id, session_id)
);

alter table diagnosis_sessions enable row level security;

drop policy if exists diagnosis_sessions_owner on diagnosis_sessions;
create policy diagnosis_sessions_owner on diagnosis_sessions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create index if not exists diagnosis_sessions_user_created_idx
  on diagnosis_sessions (user_id, created_at desc);
