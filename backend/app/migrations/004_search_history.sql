-- Search history table for storing user's search queries
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    city_name VARCHAR(255) NOT NULL,
    country_code VARCHAR(10),
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, city_name)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_searched_at ON search_history(searched_at DESC);

-- Clean up old search history (keep only last 50 per user)
-- This can be run periodically
DELETE FROM search_history
WHERE id IN (
    SELECT id FROM search_history
    WHERE user_id = $1
    ORDER BY searched_at DESC
    OFFSET 50
);
