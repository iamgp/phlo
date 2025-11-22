-- Migration: 002_auth_schema.sql
-- Create authentication schema and users table

-- Create auth schema (not exposed via PostgREST)
CREATE SCHEMA IF NOT EXISTS auth;

-- Users table
CREATE TABLE IF NOT EXISTS auth.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,  -- bcrypt hash via pgcrypto
  role VARCHAR(20) NOT NULL DEFAULT 'analyst',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE,

  CONSTRAINT valid_role CHECK (role IN ('admin', 'analyst'))
);

-- Index for login lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email) WHERE is_active = TRUE;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION auth.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION auth.update_updated_at();

-- Seed default users (passwords: admin123, analyst123)
INSERT INTO auth.users (username, email, password_hash, role)
VALUES
  ('admin', 'admin@cascade.local', crypt('admin123', gen_salt('bf')), 'admin'),
  ('analyst', 'analyst@cascade.local', crypt('analyst123', gen_salt('bf')), 'analyst')
ON CONFLICT (username) DO NOTHING;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO postgres;
