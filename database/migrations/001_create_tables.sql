-- Career Guidance API Database Schema
-- Run this in your Supabase SQL Editor

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: profiles
CREATE TABLE IF NOT EXISTS profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    email TEXT,
    experience_summary TEXT,
    skills JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: goals
CREATE TABLE IF NOT EXISTS goals (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    goal_text TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: career_data (for RAG/Vector Store)
CREATE TABLE IF NOT EXISTS career_data (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    career_title TEXT NOT NULL,
    content_chunk TEXT NOT NULL,
    embedding vector(384)  -- Size for all-MiniLM-L6-v2 model
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS career_data_embedding_idx 
ON career_data 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for career_title for faster lookups
CREATE INDEX IF NOT EXISTS career_data_title_idx ON career_data(career_title);

-- Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE career_data ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
-- Profiles: users can read/update their own profile
CREATE POLICY "Users can view own profile" 
ON profiles FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" 
ON profiles FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" 
ON profiles FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Goals: users can manage their own goals
CREATE POLICY "Users can view own goals" 
ON goals FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own goals" 
ON goals FOR ALL 
USING (auth.uid() = user_id);

-- Career_data: public read access (knowledge base)
CREATE POLICY "Anyone can read career_data" 
ON career_data FOR SELECT 
USING (true);

-- Service role can insert/update career_data (for seeding)
-- Note: Service role bypasses RLS by default

-- Function for vector similarity search (if needed)
-- You can create an RPC function for better performance:
CREATE OR REPLACE FUNCTION match_career_data(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    doc_id uuid,
    career_title text,
    content_chunk text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        career_data.doc_id,
        career_data.career_title,
        career_data.content_chunk,
        1 - (career_data.embedding <=> query_embedding) AS similarity
    FROM career_data
    WHERE 1 - (career_data.embedding <=> query_embedding) > match_threshold
    ORDER BY career_data.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

