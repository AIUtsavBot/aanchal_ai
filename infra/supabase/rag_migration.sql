-- MatruRaksha AI - Supabase pgvector Migration for Hybrid RAG
-- Run this in Supabase SQL Editor

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create maternal health embeddings table
CREATE TABLE IF NOT EXISTS maternal_health_embeddings (
    id SERIAL PRIMARY KEY,
    case_id INTEGER UNIQUE NOT NULL,
    
    -- Original data columns (for metadata filtering)
    age INTEGER NOT NULL,
    systolic_bp INTEGER NOT NULL,
    diastolic_bp INTEGER NOT NULL,
    blood_sugar NUMERIC(5,2) NOT NULL,
    body_temp NUMERIC(5,2) NOT NULL,
    heart_rate INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    
    -- Text document for BM25 (stored for reference)
    document_text TEXT NOT NULL,
    
    -- Vector embedding (768 dimensions for Gemini text-embedding-004)
    embedding vector(768),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create indexes for fast retrieval

-- Index for vector similarity search (IVFFlat - good for medium datasets)
CREATE INDEX IF NOT EXISTS maternal_embeddings_vector_idx 
ON maternal_health_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Indexes for metadata filtering
CREATE INDEX IF NOT EXISTS maternal_embeddings_age_idx ON maternal_health_embeddings(age);
CREATE INDEX IF NOT EXISTS maternal_embeddings_risk_idx ON maternal_health_embeddings(risk_level);
CREATE INDEX IF NOT EXISTS maternal_embeddings_bp_idx ON maternal_health_embeddings(systolic_bp);

-- Step 4: Create a function for vector similarity search with metadata filtering
CREATE OR REPLACE FUNCTION search_similar_maternal_cases(
    query_embedding vector(768),
    age_min INTEGER DEFAULT NULL,
    age_max INTEGER DEFAULT NULL,
    risk_filter VARCHAR(20) DEFAULT NULL,
    bp_min INTEGER DEFAULT NULL,
    bp_max INTEGER DEFAULT NULL,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    case_id INTEGER,
    age INTEGER,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    blood_sugar NUMERIC,
    body_temp NUMERIC,
    heart_rate INTEGER,
    risk_level VARCHAR,
    document_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.case_id,
        m.age,
        m.systolic_bp,
        m.diastolic_bp,
        m.blood_sugar,
        m.body_temp,
        m.heart_rate,
        m.risk_level,
        m.document_text,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM maternal_health_embeddings m
    WHERE 
        (age_min IS NULL OR m.age >= age_min)
        AND (age_max IS NULL OR m.age <= age_max)
        AND (risk_filter IS NULL OR m.risk_level = risk_filter)
        AND (bp_min IS NULL OR m.systolic_bp >= bp_min)
        AND (bp_max IS NULL OR m.systolic_bp <= bp_max)
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Step 5: Grant permissions (adjust as needed)
-- GRANT SELECT ON maternal_health_embeddings TO authenticated;
-- GRANT EXECUTE ON FUNCTION search_similar_maternal_cases TO authenticated;
