-- Initial database schema for bt-mqtt
-- This script is run automatically when the PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (migrations will handle this in production, but useful for quick setup)
-- Note: In production, use Kysely migrations instead

-- Example: Create initial user permissions
GRANT ALL PRIVILEGES ON DATABASE bt_mqtt TO btmqtt;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO btmqtt;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO btmqtt;

-- Future: Add initial seed data if needed
