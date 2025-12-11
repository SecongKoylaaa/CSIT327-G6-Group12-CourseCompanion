-- ====================================================================
-- DATABASE SCHEMA UPDATES FOR USERNAME UNIQUENESS
-- ====================================================================
-- Run this SQL in your Supabase SQL Editor to enforce username uniqueness
-- at the database level (recommended for data integrity)

-- 1. Add unique constraint to username column
-- This prevents duplicate usernames at the database level
ALTER TABLE public.users 
ADD CONSTRAINT users_username_key UNIQUE (username);

-- 2. Optional: Create case-insensitive index for better username search performance
CREATE UNIQUE INDEX users_username_lower_idx 
ON public.users (LOWER(username));

-- Note: Before running these commands, make sure there are no duplicate 
-- usernames in your existing data. You can check with:
-- SELECT username, COUNT(*) 
-- FROM public.users 
-- WHERE username IS NOT NULL
-- GROUP BY username 
-- HAVING COUNT(*) > 1;

-- ====================================================================
-- CURRENT SCHEMA (For Reference)
-- ====================================================================
-- create table public.users (
--   id bigserial not null,
--   email text not null,
--   password_hash text not null,
--   role text null,
--   created_at timestamp with time zone null default now(),
--   username text null,
--   profile_picture text null,
--   bio text null,
--   date_joined timestamp with time zone null default now(),
--   last_login timestamp with time zone null,
--   constraint users_pkey primary key (id),
--   constraint users_email_key unique (email),
--   constraint users_username_key unique (username)  -- ADD THIS
-- ) TABLESPACE pg_default;
