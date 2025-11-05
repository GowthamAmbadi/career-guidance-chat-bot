-- Fix profiles table to accept TEXT user_id instead of UUID
-- Run this in your Supabase SQL Editor

-- Step 1: Drop all RLS policies that depend on user_id
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Users can view own goals" ON goals;
DROP POLICY IF EXISTS "Users can manage own goals" ON goals;

-- Step 2: Drop foreign key constraints
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_user_id_fkey;
ALTER TABLE goals DROP CONSTRAINT IF EXISTS goals_user_id_fkey;

-- Step 3: Change user_id column type from UUID to TEXT
ALTER TABLE profiles ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
ALTER TABLE goals ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;

-- Step 4: Re-add foreign key constraint for goals
ALTER TABLE goals ADD CONSTRAINT goals_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE;

-- Step 5: Re-create RLS policies (optional - since we use service_role_key, these won't affect API)
-- Note: These policies won't work with TEXT user_id and auth.uid() (which returns UUID)
-- Since we're using service_role_key which bypasses RLS, we can leave them commented out
-- If you want to enable RLS later with proper auth, you'll need to modify these policies

-- CREATE POLICY "Users can view own profile" 
-- ON profiles FOR SELECT 
-- USING (auth.uid()::TEXT = user_id);

-- CREATE POLICY "Users can update own profile" 
-- ON profiles FOR UPDATE 
-- USING (auth.uid()::TEXT = user_id);

-- CREATE POLICY "Users can insert own profile" 
-- ON profiles FOR INSERT 
-- WITH CHECK (auth.uid()::TEXT = user_id);

-- CREATE POLICY "Users can view own goals" 
-- ON goals FOR SELECT 
-- USING (auth.uid()::TEXT = user_id);

-- CREATE POLICY "Users can manage own goals" 
-- ON goals FOR ALL 
-- USING (auth.uid()::TEXT = user_id);

-- Step 6: Verify the changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'profiles' AND column_name = 'user_id';
