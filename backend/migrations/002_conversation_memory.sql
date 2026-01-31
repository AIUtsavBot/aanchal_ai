-- Conversation Memory Tables for Intelligent Follow-up
-- Run this in Supabase SQL Editor

-- Enable pgvector extension (already enabled in most Supabase projects)
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing conversation summaries with embeddings
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id SERIAL PRIMARY KEY,
    mother_id UUID REFERENCES mothers(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    topics JSONB DEFAULT '[]',
    symptoms JSONB DEFAULT '[]',
    advice_given TEXT,
    embedding vector(768), -- Gemini text-embedding-004 dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_conv_summaries_mother ON conversation_summaries(mother_id);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_created ON conversation_summaries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_topics ON conversation_summaries USING GIN(topics);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_symptoms ON conversation_summaries USING GIN(symptoms);

-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_conv_summaries_embedding ON conversation_summaries 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS Policies
ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON conversation_summaries
    FOR ALL USING (true);

CREATE POLICY "Authenticated users read own" ON conversation_summaries
    FOR SELECT USING (auth.uid()::text = mother_id::text);


-- Function for semantic similarity search
CREATE OR REPLACE FUNCTION search_similar_conversations(
    query_embedding vector(768),
    mother_id_param TEXT,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id INT,
    mother_id UUID,
    summary TEXT,
    topics JSONB,
    symptoms JSONB,
    advice_given TEXT,
    created_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.id,
        cs.mother_id,
        cs.summary,
        cs.topics,
        cs.symptoms,
        cs.advice_given,
        cs.created_at,
        1 - (cs.embedding <=> query_embedding) AS similarity
    FROM conversation_summaries cs
    WHERE 
        cs.mother_id::text = mother_id_param
        AND cs.embedding IS NOT NULL
        AND 1 - (cs.embedding <=> query_embedding) > match_threshold
    ORDER BY cs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- Function to search by topics (fallback when no embedding)
CREATE OR REPLACE FUNCTION search_conversations_by_topics(
    mother_id_param TEXT,
    search_topics TEXT[],
    days_back INT DEFAULT 90,
    limit_count INT DEFAULT 5
)
RETURNS TABLE (
    id INT,
    mother_id UUID,
    summary TEXT,
    topics JSONB,
    symptoms JSONB,
    advice_given TEXT,
    created_at TIMESTAMPTZ,
    topic_overlap INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.id,
        cs.mother_id,
        cs.summary,
        cs.topics,
        cs.symptoms,
        cs.advice_given,
        cs.created_at,
        (
            SELECT COUNT(*)::INT 
            FROM jsonb_array_elements_text(cs.topics) t 
            WHERE LOWER(t) = ANY(ARRAY(SELECT LOWER(unnest(search_topics))))
        ) AS topic_overlap
    FROM conversation_summaries cs
    WHERE 
        cs.mother_id::text = mother_id_param
        AND cs.created_at > NOW() - (days_back || ' days')::INTERVAL
    ORDER BY topic_overlap DESC, cs.created_at DESC
    LIMIT limit_count;
END;
$$;

-- Add index to telegram_logs for faster message search
CREATE INDEX IF NOT EXISTS idx_telegram_logs_mother_content 
    ON telegram_logs(mother_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_telegram_logs_content_search 
    ON telegram_logs USING gin(to_tsvector('simple', message_content));


-- Grant permissions
GRANT SELECT, INSERT ON conversation_summaries TO authenticated;
GRANT SELECT, INSERT ON conversation_summaries TO service_role;
GRANT EXECUTE ON FUNCTION search_similar_conversations TO authenticated;
GRANT EXECUTE ON FUNCTION search_similar_conversations TO service_role;
GRANT EXECUTE ON FUNCTION search_conversations_by_topics TO authenticated;
GRANT EXECUTE ON FUNCTION search_conversations_by_topics TO service_role;
