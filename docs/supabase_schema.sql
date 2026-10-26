-- Run in Supabase SQL Editor. This schema is for the internship demo backend.
create table if not exists public.trips (
  id text primary key,
  title text not null,
  destination text not null,
  created_at timestamptz not null default now(),
  payload jsonb not null
);
create index if not exists trips_created_at_idx on public.trips (created_at desc);
-- IMPORTANT: This demo uses the service-role key on the server. Do not expose it in the browser.
-- Before production, implement Supabase Auth and enable RLS with per-user ownership policies.
