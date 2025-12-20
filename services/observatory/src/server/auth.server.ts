/**
 * Authentication middleware for Observatory server functions
 *
 * ADR: 0026-observatory-auth-and-realtime.md
 * Bead: phlo-h2c
 *
 * When OBSERVATORY_AUTH_ENABLED=true, all server functions require
 * a valid token via X-Observatory-Token header or auth.token in settings.
 */

/**
 * Check if authentication is enabled
 */
export function isAuthEnabled(): boolean {
  return process.env.OBSERVATORY_AUTH_ENABLED === 'true'
}

/**
 * Get the expected auth token from environment
 */
function getExpectedToken(): string | undefined {
  return process.env.OBSERVATORY_AUTH_TOKEN
}

/**
 * Auth error result type
 */
export interface AuthError {
  error: string
  status: 401
}

/**
 * Check if a result is an auth error
 */
export function isAuthError(result: unknown): result is AuthError {
  return (
    typeof result === 'object' &&
    result !== null &&
    'status' in result &&
    (result as AuthError).status === 401
  )
}

/**
 * Validate auth token
 *
 * Returns undefined if auth passes, or an AuthError if it fails.
 * When auth is disabled, always returns undefined (passes).
 *
 * @param token - The token to validate (from header or settings)
 * @returns undefined if valid, AuthError if invalid
 */
export function validateAuth(token?: string): AuthError | undefined {
  // Auth disabled - always pass
  if (!isAuthEnabled()) {
    return undefined
  }

  const expectedToken = getExpectedToken()

  // No token configured on server - auth is misconfigured
  if (!expectedToken) {
    console.warn(
      '[auth] OBSERVATORY_AUTH_ENABLED=true but OBSERVATORY_AUTH_TOKEN is not set',
    )
    return { error: 'Authentication misconfigured', status: 401 }
  }

  // No token provided by client
  if (!token) {
    return { error: 'Authentication required', status: 401 }
  }

  // Token mismatch
  if (token !== expectedToken) {
    return { error: 'Invalid authentication token', status: 401 }
  }

  // Auth passed
  return undefined
}

/**
 * Create an auth-protected wrapper for server function handlers
 *
 * Usage:
 * ```ts
 * export const getAssets = createServerFn()
 *   .inputValidator((input: { authToken?: string }) => input)
 *   .handler(withAuth(async ({ data }) => {
 *     // ... handler logic
 *   }))
 * ```
 */
export function withAuth<TInput extends { authToken?: string }, TOutput>(
  handler: (ctx: { data: TInput }) => Promise<TOutput>,
): (ctx: { data: TInput }) => Promise<TOutput | AuthError> {
  return async (ctx) => {
    const authError = validateAuth(ctx.data.authToken)
    if (authError) {
      return authError
    }
    return handler(ctx)
  }
}
