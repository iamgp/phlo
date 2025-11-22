-- Migration: 006_roles_and_rls.sql
-- Create PostgreSQL roles and Row-Level Security policies

-- ============================================================================
-- PostgreSQL Roles
-- ============================================================================

-- Create authenticator role (used by PostgREST to connect)
-- This role can switch to other roles based on JWT claims
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
    CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'authenticator_password_change_in_production';
  END IF;
END
$$;

-- Create anon role (for unauthenticated requests)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
END
$$;

-- Create authenticated role (base role for authenticated users)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
END
$$;

-- Create analyst role (inherits from authenticated)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analyst') THEN
    CREATE ROLE analyst NOLOGIN IN ROLE authenticated;
  END IF;
END
$$;

-- Create admin role (inherits from authenticated)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin NOLOGIN IN ROLE authenticated;
  END IF;
END
$$;

-- Grant authenticator ability to switch to these roles
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT analyst TO authenticator;
GRANT admin TO authenticator;

-- ============================================================================
-- Schema Permissions
-- ============================================================================

-- Grant schema usage
GRANT USAGE ON SCHEMA api TO anon, authenticated;
GRANT USAGE ON SCHEMA auth TO authenticator;

-- Grant table/view permissions
GRANT SELECT ON api.glucose_readings TO authenticated;
GRANT SELECT ON api.glucose_daily_summary TO authenticated;
GRANT SELECT ON api.glucose_hourly_patterns TO authenticated;

-- Grant function execution
GRANT EXECUTE ON FUNCTION api.login TO anon;  -- Login doesn't require auth
GRANT EXECUTE ON FUNCTION api.glucose_statistics TO authenticated;
GRANT EXECUTE ON FUNCTION api.user_info TO authenticated;
GRANT EXECUTE ON FUNCTION api.health TO anon;  -- Health check is public

-- ============================================================================
-- Row-Level Security Policies
-- ============================================================================

-- Note: Views don't support RLS directly in PostgreSQL, but we can secure
-- the underlying tables or use security definer functions

-- For demonstration, we'll create policies on the views
-- (In production, you'd apply RLS to the underlying marts tables)

-- Policy: Authenticated users can read all glucose data
-- Since our views are read-only and based on marts tables,
-- we control access via GRANT statements above

-- If we needed row-level restrictions, we could do:
-- CREATE POLICY authenticated_read ON api.glucose_readings
--   FOR SELECT TO authenticated
--   USING (true);  -- Allow all rows for authenticated users

-- For admin-only operations (future):
-- CREATE POLICY admin_only ON some_table
--   FOR ALL TO admin
--   USING (true)
--   WITH CHECK (true);

-- ============================================================================
-- Additional Security Settings
-- ============================================================================

-- Ensure auth schema is private
REVOKE ALL ON SCHEMA auth FROM PUBLIC;
REVOKE ALL ON auth.users FROM PUBLIC;

-- Only specific functions can access auth.users
REVOKE ALL ON auth.users FROM anon, authenticated, analyst, admin;

COMMENT ON ROLE authenticator IS 'PostgREST connection role that can switch to other roles';
COMMENT ON ROLE anon IS 'Unauthenticated requests';
COMMENT ON ROLE authenticated IS 'Base role for authenticated users';
COMMENT ON ROLE analyst IS 'Analyst role with read access to glucose data';
COMMENT ON ROLE admin IS 'Admin role with full access';
