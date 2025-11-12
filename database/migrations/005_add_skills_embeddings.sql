-- Migration: Add skills_embeddings column to profiles table
-- Run this in your Supabase SQL Editor
-- This adds vector embeddings for each skill to enable semantic skill matching

-- Add skills_embeddings column (array of vectors, one per skill)
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS skills_embeddings vector(1536)[];

-- Note: We don't create an index on skills_embeddings because:
-- 1. GIN indexes on large vector arrays exceed PostgreSQL's index row size limit
-- 2. Our queries use unnest() which doesn't require an index
-- 3. The array size (26 skills × 1536 dimensions) is too large for indexing
-- Queries will still work, just without index acceleration (acceptable for this use case)

-- Function to find similar skills using vector similarity
-- This function takes a skill embedding and finds profiles with similar skills
CREATE OR REPLACE FUNCTION find_similar_skills(
    query_skill_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    user_id text,
    name text,
    matched_skill text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        profiles.user_id::text,
        profiles.name,
        -- Extract the skill name from the skills array at the same index
        profiles.skills->>(idx - 1) AS matched_skill,
        similarity_score AS similarity
    FROM profiles,
    LATERAL (
        SELECT 
            idx,
            1 - (skill_emb <=> query_skill_embedding) AS similarity_score
        FROM unnest(profiles.skills_embeddings) WITH ORDINALITY AS skill_emb(skill_vec, idx)
        WHERE 1 - (skill_vec <=> query_skill_embedding) > similarity_threshold
        ORDER BY skill_vec <=> query_skill_embedding
        LIMIT 1
    ) AS best_match
    WHERE profiles.skills_embeddings IS NOT NULL
      AND array_length(profiles.skills_embeddings, 1) > 0
    ORDER BY similarity DESC
    LIMIT max_results;
END;
$$;

-- Function to calculate skill similarity between two skill arrays
CREATE OR REPLACE FUNCTION calculate_skill_array_similarity(
    skills1_embeddings vector(1536)[],
    skills2_embeddings vector(1536)[]
)
RETURNS float
LANGUAGE plpgsql
AS $$
DECLARE
    total_similarity float := 0.0;
    max_similarity float;
    skill1_vec vector(1536);
    skill2_vec vector(1536);
    match_count int := 0;
BEGIN
    -- For each skill in skills1, find the best matching skill in skills2
    FOREACH skill1_vec IN ARRAY skills1_embeddings
    LOOP
        max_similarity := 0.0;
        
        -- Find the best match in skills2
        FOREACH skill2_vec IN ARRAY skills2_embeddings
        LOOP
            max_similarity := GREATEST(max_similarity, 1 - (skill1_vec <=> skill2_vec));
        END LOOP;
        
        -- Only count matches above threshold (0.7 = 70% similarity)
        IF max_similarity >= 0.7 THEN
            total_similarity := total_similarity + max_similarity;
            match_count := match_count + 1;
        END IF;
    END LOOP;
    
    -- Return average similarity (0 if no matches)
    IF match_count > 0 THEN
        RETURN total_similarity / match_count;
    ELSE
        RETURN 0.0;
    END IF;
END;
$$;

-- Function to update skills_embeddings via RPC (for Supabase REST API compatibility)
-- This function accepts embeddings as JSONB array and converts to vector array
CREATE OR REPLACE FUNCTION update_skills_embeddings(
    p_user_id text,
    p_skills_embeddings jsonb
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    vec_array vector(1536)[];
    emb_json jsonb;
    vec_str text;
    float_array float[];
BEGIN
    -- Convert JSONB array to vector array
    vec_array := ARRAY[]::vector(1536)[];
    
    -- Iterate through each embedding (each is a JSONB array of floats)
    FOR emb_json IN SELECT * FROM jsonb_array_elements(p_skills_embeddings)
    LOOP
        -- Convert JSONB array to PostgreSQL float array
        SELECT ARRAY(SELECT jsonb_array_elements_text(emb_json)::float) INTO float_array;
        
        -- Convert float array to vector string format: "[0.1,0.2,...]"
        vec_str := '[' || array_to_string(float_array, ',') || ']';
        
        -- Append to vector array
        vec_array := array_append(vec_array, vec_str::vector(1536));
    END LOOP;
    
    -- Update the profile
    UPDATE profiles
    SET skills_embeddings = vec_array
    WHERE user_id::text = p_user_id;
END;
$$;

