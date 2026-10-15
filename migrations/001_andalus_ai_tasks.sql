-- Andalus AI task queue. Apply to the academy Supabase project.
create table if not exists public.andalus_ai_tasks (
 id uuid primary key default gen_random_uuid(),
 title text not null check (char_length(btrim(title)) between 1 and 180),
 details text not null default '',
 task_type text not null default 'admin',
 status text not null default 'pending' check (status in ('pending','scheduled','running','completed','failed','cancelled')),
 run_at timestamptz,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 executed_at timestamptz,
 result jsonb not null default '{}'::jsonb
);
create index if not exists andalus_ai_tasks_due_idx on public.andalus_ai_tasks(run_at) where status='scheduled';
create index if not exists andalus_ai_tasks_status_idx on public.andalus_ai_tasks(status,created_at desc);
alter table public.andalus_ai_tasks enable row level security;
-- No client policies; service-role access stays server-side only.
