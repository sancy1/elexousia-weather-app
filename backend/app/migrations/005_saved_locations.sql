-- Saved locations table for storing user's favorite locations
CREATE TABLE IF NOT EXISTS saved_locations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    city_name VARCHAR(255) NOT NULL,
    country_code VARCHAR(10),
    label VARCHAR(50) NOT NULL DEFAULT 'Home',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_saved_locations_user_id ON saved_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_locations_display_order ON saved_locations(user_id, display_order);
CREATE INDEX IF NOT EXISTS idx_saved_locations_city_name ON saved_locations(city_name);

-- Unique constraint to prevent duplicate locations per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_locations_user_city ON saved_locations(user_id, city_name);
