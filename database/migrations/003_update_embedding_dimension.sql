-- Migration: Update embedding dimension from 384 to 1536 for OpenAI embeddings
-- Run this in your Supabase SQL Editor

-- Drop the old index
DROP INDEX IF EXISTS career_data_embedding_idx;

-- Alter the embedding column to support 1536 dimensions (OpenAI text-embedding-3-small)
-- Note: This will fail if there's existing data, so clear the table first
ALTER TABLE career_data 
ALTER COLUMN embedding TYPE vector(1536);

-- Recreate the index with new dimension
CREATE INDEX IF NOT EXISTS career_data_embedding_idx 
ON career_data 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Update the RPC function to use new dimension
CREATE OR REPLACE FUNCTION match_career_data(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.3,
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

