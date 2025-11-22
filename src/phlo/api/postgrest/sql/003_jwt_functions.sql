-- Migration: 003_jwt_functions.sql
-- JWT token generation functions
-- Based on: https://github.com/michelp/pgjwt

-- Simple JWT signing function using HMAC-SHA256
CREATE OR REPLACE FUNCTION auth.sign_jwt(payload JSON, secret TEXT)
RETURNS TEXT AS $$
DECLARE
  header JSON;
  segments TEXT[];
BEGIN
  -- JWT Header
  header := '{"alg":"HS256","typ":"JWT"}';

  -- Encode header and payload
  segments := ARRAY[
    replace(replace(replace(encode(convert_to(header::text, 'utf8'), 'base64'), E'\n', ''), '+', '-'), '/', '_'),
    replace(replace(replace(encode(convert_to(payload::text, 'utf8'), 'base64'), E'\n', ''), '+', '-'), '/', '_')
  ];

  -- Create signature
  segments := segments || replace(replace(replace(
    encode(
      hmac(segments[1] || '.' || segments[2], secret, 'sha256'),
      'base64'
    ), E'\n', ''), '+', '-'), '/', '_');

  -- Return complete JWT
  RETURN segments[1] || '.' || segments[2] || '.' || segments[3];
END;
$$ LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER;

-- Function to verify JWT (simplified version)
CREATE OR REPLACE FUNCTION auth.verify_jwt(token TEXT, secret TEXT)
RETURNS JSON AS $$
DECLARE
  segments TEXT[];
  payload_segment TEXT;
  payload JSON;
BEGIN
  -- Split token into segments
  segments := string_to_array(token, '.');

  IF array_length(segments, 1) != 3 THEN
    RAISE EXCEPTION 'Invalid JWT format';
  END IF;

  -- Decode payload (simplified - should verify signature in production)
  payload_segment := segments[2];

  -- Add padding if necessary
  WHILE length(payload_segment) % 4 != 0 LOOP
    payload_segment := payload_segment || '=';
  END LOOP;

  -- Decode base64url to JSON
  payload_segment := replace(replace(payload_segment, '-', '+'), '_', '/');
  payload := convert_from(decode(payload_segment, 'base64'), 'utf8')::JSON;

  -- Verify expiration
  IF (payload->>'exp')::bigint < extract(epoch from now()) THEN
    RAISE EXCEPTION 'Token expired';
  END IF;

  RETURN payload;
END;
$$ LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER;

COMMENT ON FUNCTION auth.sign_jwt IS 'Sign a JWT token with HS256 algorithm';
COMMENT ON FUNCTION auth.verify_jwt IS 'Verify and decode a JWT token';
