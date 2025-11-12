-- Migration: Fix skills_embeddings index issue
-- Run this in your Supabase SQL Editor
-- This removes the GIN index that was causing "index row size exceeds maximum" errors

-- Drop the problematic GIN index
DROP INDEX IF EXISTS profiles_skills_embeddings_idx;

-- Note: We don't recreate the index because:
-- 1. GIN indexes on large vector arrays exceed PostgreSQL's index row size limit (2712 bytes)
-- 2. With 26 skills × 1536 dimensions, the total size is ~6160 bytes, which exceeds the limit
-- 3. Our queries use unnest() which works fine without an index
-- 4. The performance impact is acceptable since we're querying individual profiles, not scanning large tables

