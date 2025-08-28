-- CannaBot PostgreSQL Database Initialization
-- This script sets up the initial database structure

-- Create database (this will be created by the container)
-- CREATE DATABASE cannabot;

-- Connect to the cannabot database
\c cannabot;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create initial tables will be handled by the application
-- The bot will create tables automatically using the schema

-- Grant permissions to cannabot user
GRANT ALL PRIVILEGES ON DATABASE cannabot TO cannabot;
GRANT ALL PRIVILEGES ON SCHEMA public TO cannabot;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cannabot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cannabot;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cannabot;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cannabot;

-- Log successful initialization
SELECT 'CannaBot database initialized successfully!' AS status;
