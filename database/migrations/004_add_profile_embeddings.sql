-- Migration: Add profile_embedding column to profiles table
-- Run this in your Supabase SQL Editor

-- Add profile_embedding column (entire profile as vector)
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS profile_embedding vector(1536);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS profiles_embedding_idx 
ON profiles 
USING ivfflat (profile_embedding vector_cosine_ops)
WITH (lists = 100);

-- Function for profile similarity search
CREATE OR REPLACE FUNCTION match_profiles(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    user_id text,
    name text,
    profile_similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        profiles.user_id,
        profiles.name,
        1 - (profiles.profile_embedding <=> query_embedding) AS profile_similarity
    FROM profiles
    WHERE profiles.profile_embedding IS NOT NULL
      AND 1 - (profiles.profile_embedding <=> query_embedding) > match_threshold
    ORDER BY profiles.profile_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

