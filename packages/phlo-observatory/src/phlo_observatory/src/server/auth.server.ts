/**
 * Authentication middleware for Observatory server functions
 *
 * ADR: 0026-observatory-auth-and-realtime.md
 * Bead: phlo-h2c
 *
 * Uses TanStack Start's createMiddleware to provide reusable auth
 * that can be chained with any server function.
 *
 * Usage:
 * ```ts
 * import { authMiddleware } from '@/server/auth.server'
 *
 * export const getAssets = createServerFn()
 *   .middleware([authMiddleware])
 *   .handler(async ({ context }) => {
 *     // context.isAuthenticated is available
 *     // Auth already validated if OBSERVATORY_AUTH_ENABLED=true
 *   })
 * ```
 */

import { createMiddleware } from '@tanstack/react-start'

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
 */
export function validateAuth(token?: string): AuthError | undefined {
  if (!isAuthEnabled()) {
    return undefined
  }

  const expectedToken = getExpectedToken()

  if (!expectedToken) {
    console.warn(
      '[auth] OBSERVATORY_AUTH_ENABLED=true but OBSERVATORY_AUTH_TOKEN is not set',
    )
    return { error: 'Authentication misconfigured', status: 401 }
  }

  if (!token) {
    return { error: 'Authentication required', status: 401 }
  }

  if (token !== expectedToken) {
    return { error: 'Invalid authentication token', status: 401 }
  }

  return undefined
}

/**
 * Auth middleware for server functions
 *
 * Add to any server function with .middleware([authMiddleware])
 * Validates authToken from input when OBSERVATORY_AUTH_ENABLED=true
 */
export const authMiddleware = createMiddleware({ type: 'function' })
  .inputValidator((input: { authToken?: string }) => input)
  .server(async ({ next, data }) => {
    const authError = validateAuth(data.authToken)

    if (authError) {
      // Throw error to stop execution chain
      throw new Error(authError.error)
    }

    return next({
      context: {
        isAuthenticated: isAuthEnabled(),
      },
    })
  })

/**
 * Legacy withAuth wrapper - kept for backward compatibility
 * Prefer using .middleware([authMiddleware]) instead
 */
export function withAuth<
  TInput extends { authToken?: string },
  TOutput extends object,
>(
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
