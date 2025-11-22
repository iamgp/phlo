-- Migration: 005_api_functions.sql
-- Create API functions for authentication and computed endpoints

-- Function: Login (replaces /api/v1/auth/login)
CREATE OR REPLACE FUNCTION api.login(username TEXT, password TEXT)
RETURNS JSON AS $$
DECLARE
  user_record RECORD;
  token TEXT;
  jwt_secret TEXT;
  payload JSON;
BEGIN
  -- Get JWT secret from environment (set in PostgREST config)
  jwt_secret := current_setting('app.settings.jwt_secret', true);

  IF jwt_secret IS NULL OR jwt_secret = '' THEN
    jwt_secret := 'your-secret-key-min-32-characters-long-replace-in-production';
  END IF;

  -- Validate credentials
  SELECT * INTO user_record
  FROM auth.users
  WHERE auth.users.username = login.username
    AND auth.users.is_active = TRUE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Invalid credentials'
      USING HINT = 'Please check your username and password';
  END IF;

  -- Verify password using pgcrypto crypt function
  IF NOT (user_record.password_hash = crypt(password, user_record.password_hash)) THEN
    RAISE EXCEPTION 'Invalid credentials'
      USING HINT = 'Please check your username and password';
  END IF;

  -- Build JWT payload
  payload := json_build_object(
    'user_id', user_record.user_id,
    'username', user_record.username,
    'email', user_record.email,
    'role', user_record.role,
    'exp', extract(epoch from now() + interval '60 minutes')::bigint,
    'iat', extract(epoch from now())::bigint,
    'https://hasura.io/jwt/claims', json_build_object(
      'x-hasura-allowed-roles', json_build_array(user_record.role),
      'x-hasura-default-role', user_record.role,
      'x-hasura-user-id', user_record.user_id::text
    )
  );

  -- Generate JWT token
  token := auth.sign_jwt(payload, jwt_secret);

  -- Return response matching FastAPI format
  RETURN json_build_object(
    'access_token', token,
    'token_type', 'Bearer',
    'expires_in', 3600,
    'user', json_build_object(
      'user_id', user_record.user_id,
      'username', user_record.username,
      'email', user_record.email,
      'role', user_record.role
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Glucose Statistics (replaces /api/v1/glucose/statistics)
CREATE OR REPLACE FUNCTION api.glucose_statistics(period_days INT DEFAULT 30)
RETURNS JSON AS $$
DECLARE
  result JSON;
  start_date DATE;
BEGIN
  -- Validate input
  IF period_days <= 0 THEN
    RAISE EXCEPTION 'period_days must be positive';
  END IF;

  IF period_days > 365 THEN
    RAISE EXCEPTION 'period_days cannot exceed 365';
  END IF;

  start_date := CURRENT_DATE - (period_days || ' days')::interval;

  -- Calculate statistics
  SELECT json_build_object(
    'period_days', period_days,
    'start_date', start_date,
    'end_date', CURRENT_DATE,
    'avg_glucose_mg_dl', ROUND(AVG(avg_glucose_mg_dl), 1),
    'min_glucose_mg_dl', MIN(min_glucose_mg_dl),
    'max_glucose_mg_dl', MAX(max_glucose_mg_dl),
    'avg_time_in_range_pct', ROUND(AVG(time_in_range_pct), 1),
    'avg_time_below_range_pct', ROUND(AVG(time_below_range_pct), 1),
    'avg_time_above_range_pct', ROUND(AVG(time_above_range_pct), 1),
    'avg_estimated_a1c_pct', ROUND(AVG(estimated_a1c_pct), 2),
    'avg_coefficient_of_variation', ROUND(AVG(coefficient_of_variation), 1),
    'total_readings', SUM(reading_count),
    'days_with_data', COUNT(*)
  ) INTO result
  FROM marts.mrt_glucose_overview
  WHERE reading_date >= start_date;

  RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Current User Info (replaces /api/v1/metadata/user/me)
CREATE OR REPLACE FUNCTION api.user_info()
RETURNS JSON AS $$
DECLARE
  jwt_claims JSON;
BEGIN
  -- Get JWT claims from PostgREST (set in request.jwt.claims)
  BEGIN
    jwt_claims := current_setting('request.jwt.claims', true)::JSON;
  EXCEPTION
    WHEN undefined_object THEN
      RAISE EXCEPTION 'Not authenticated'
        USING HINT = 'Please provide a valid JWT token';
  END;

  IF jwt_claims IS NULL THEN
    RAISE EXCEPTION 'Not authenticated'
      USING HINT = 'Please provide a valid JWT token';
  END IF;

  -- Return user information from JWT claims
  RETURN json_build_object(
    'user_id', jwt_claims->>'user_id',
    'username', jwt_claims->>'username',
    'email', jwt_claims->>'email',
    'role', jwt_claims->>'role'
  );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Function: Health Check
CREATE OR REPLACE FUNCTION api.health()
RETURNS JSON AS $$
BEGIN
  RETURN json_build_object(
    'status', 'healthy',
    'timestamp', NOW(),
    'service', 'phlo-postgrest',
    'database', current_database()
  );
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION api.login TO postgres;
GRANT EXECUTE ON FUNCTION api.glucose_statistics TO postgres;
GRANT EXECUTE ON FUNCTION api.user_info TO postgres;
GRANT EXECUTE ON FUNCTION api.health TO postgres;

-- Comments for documentation
COMMENT ON FUNCTION api.login IS 'Authenticate user and return JWT token';
COMMENT ON FUNCTION api.glucose_statistics IS 'Calculate glucose statistics for specified period';
COMMENT ON FUNCTION api.user_info IS 'Get current authenticated user information';
COMMENT ON FUNCTION api.health IS 'Health check endpoint';
