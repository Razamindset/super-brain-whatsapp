-- ============================================================
-- Super Brain - Reminders Table
-- Run in Supabase SQL Editor
-- ============================================================

CREATE TABLE IF NOT EXISTS public.reminders (
  id          text PRIMARY KEY,          -- UUID, also used as APScheduler job_id
  user_id     text REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  text        text NOT NULL,
  run_at      timestamp with time zone NOT NULL,
  status      text NOT NULL DEFAULT 'pending',  -- 'pending' | 'fired' | 'cancelled'
  created_at  timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for fast per-user pending lookups
CREATE INDEX IF NOT EXISTS idx_reminders_user_status
  ON public.reminders(user_id, status);
