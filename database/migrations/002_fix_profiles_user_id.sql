-- Fix profiles table to accept TEXT user_id instead of UUID
-- This allows us to use custom user_ids from localStorage without Supabase Auth

-- Drop the foreign key constraint first
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_user_id_fkey;

-- Drop the primary key constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_pkey;

-- Change user_id column type from UUID to TEXT
ALTER TABLE profiles ALTER COLUMN user_id TYPE TEXT;

-- Re-add primary key constraint
ALTER TABLE profiles ADD PRIMARY KEY (user_id);

-- Update goals table to also use TEXT user_id
ALTER TABLE goals DROP CONSTRAINT IF EXISTS goals_user_id_fkey;
ALTER TABLE goals ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE goals ADD CONSTRAINT goals_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE;

-- Update RLS policies to work with TEXT user_id
-- Note: These policies won't work without auth, so we'll disable RLS or use service role
-- For now, we'll use service role key which bypasses RLS

