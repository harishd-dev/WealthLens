-- ═══════════════════════════════════════════════════════════════════════════
-- WealthLens — Supabase PostgreSQL Schema
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query
-- ═══════════════════════════════════════════════════════════════════════════

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ── transactions ─────────────────────────────────────────────────────────────
create table if not exists public.transactions (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references auth.users(id) on delete cascade,
    description text not null,
    amount      numeric(12,2) not null check (amount > 0),
    type        text not null check (type in ('debit','credit')),
    category    text not null default 'Other',
    date        date not null,
    notes       text,
    source      text not null default 'manual',   -- 'manual' | 'upload'
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists idx_tx_user_date     on public.transactions(user_id, date desc);
create index if not exists idx_tx_user_category on public.transactions(user_id, category);
create index if not exists idx_tx_user_type     on public.transactions(user_id, type);

-- Auto-update updated_at
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger tx_updated_at
  before update on public.transactions
  for each row execute procedure public.set_updated_at();

-- ── merchant_mappings (learning table) ───────────────────────────────────────
create table if not exists public.merchant_mappings (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references auth.users(id) on delete cascade,
    merchant_key text not null,   -- lowercase keyword e.g. "swiggy"
    category     text not null,
    created_at   timestamptz not null default now(),
    unique(user_id, merchant_key)
);

create index if not exists idx_mm_user on public.merchant_mappings(user_id);

-- ── Row Level Security ───────────────────────────────────────────────────────
-- Users can only read/write their own data.

alter table public.transactions      enable row level security;
alter table public.merchant_mappings enable row level security;

-- transactions policies
create policy "Users read own transactions"
  on public.transactions for select
  using (auth.uid() = user_id);

create policy "Users insert own transactions"
  on public.transactions for insert
  with check (auth.uid() = user_id);

create policy "Users update own transactions"
  on public.transactions for update
  using (auth.uid() = user_id);

create policy "Users delete own transactions"
  on public.transactions for delete
  using (auth.uid() = user_id);

-- merchant_mappings policies
create policy "Users read own mappings"
  on public.merchant_mappings for select
  using (auth.uid() = user_id);

create policy "Users insert own mappings"
  on public.merchant_mappings for insert
  with check (auth.uid() = user_id);

create policy "Users update own mappings"
  on public.merchant_mappings for update
  using (auth.uid() = user_id);

create policy "Users delete own mappings"
  on public.merchant_mappings for delete
  using (auth.uid() = user_id);

-- ── Helpful views (optional, for analytics queries) ──────────────────────────
create or replace view public.monthly_summary as
select
  user_id,
  date_trunc('month', date)::date          as month,
  sum(case when type='credit' then amount else 0 end) as income,
  sum(case when type='debit'  then amount else 0 end) as expense,
  sum(case when type='credit' then amount else -amount end) as net
from public.transactions
group by user_id, date_trunc('month', date);

create or replace view public.category_summary as
select
  user_id,
  category,
  count(*)::int                              as tx_count,
  sum(amount)                                as total,
  avg(amount)                                as avg_amount,
  max(date)                                  as last_used
from public.transactions
where type = 'debit'
group by user_id, category;
