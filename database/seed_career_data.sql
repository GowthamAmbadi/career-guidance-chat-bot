-- Sample career data for seeding the knowledge base
-- This is a basic example - you should expand this with real career data

-- Note: Embeddings need to be generated using the embedding model
-- This script shows the structure, but you'll need to generate embeddings programmatically
-- See: scripts/seed_career_data.py for a Python script to do this

INSERT INTO career_data (career_title, content_chunk, embedding) VALUES
-- Example structure (embeddings would be real vectors)
('Data Scientist', 
 'Data Scientists analyze complex data sets to identify trends and patterns. 
They use machine learning, statistics, and programming (Python, R) to build predictive models. 
Salary range: $95,000 - $165,000. Strong job outlook with 22% growth projected.',
 -- embedding would be a 384-dimensional vector here
 NULL),
('Software Engineer',
 'Software Engineers design, develop, and maintain software applications. 
They work with languages like Python, Java, JavaScript, and use frameworks like React, Django, Spring. 
Salary range: $85,000 - $150,000. Excellent job outlook with high demand.',
 NULL);

-- Note: To properly seed, you should:
-- 1. Use the embedding model to generate embeddings for each content_chunk
-- 2. Insert the actual vector values instead of NULL
-- See scripts/seed_career_data.py for a complete solution

