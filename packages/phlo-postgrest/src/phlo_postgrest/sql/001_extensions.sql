-- Migration: 001_extensions.sql
-- Install required PostgreSQL extensions for PostgREST
-- pgcrypto: For password hashing
-- pgjwt: For JWT token generation

-- Enable pgcrypto extension (for password hashing)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Note: pgjwt extension needs to be installed separately
-- For now, we'll use a custom JWT signing function
-- Install instructions: https://github.com/michelp/pgjwt

-- Verify extensions
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('pgcrypto');
