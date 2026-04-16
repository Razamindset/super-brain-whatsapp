-- ============================================================
-- Super Brain - Migration: Add Onboarding Fields to Users
-- Run this if you already ran 001_initial_schema.sql
-- ============================================================

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS name text,
  ADD COLUMN IF NOT EXISTS preferences jsonb DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS is_onboarded boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS onboarding_step text DEFAULT 'start';
