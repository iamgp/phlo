/**
 * Phlo API Server Client
 *
 * Helper for server functions to call the Python phlo-api backend.
 * Handles URL resolution for both Docker and local dev environments.
 */

const PHLO_API_URL = process.env.PHLO_API_URL || 'http://localhost:4000'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

interface RequestOptions {
  method?: HttpMethod
  params?: Record<string, string | number | boolean | undefined>
  body?: unknown
  timeoutMs?: number
}

/**
 * Internal request handler - all HTTP methods go through here
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = 'GET', params, body, timeoutMs = 30000 } = options

  const url = new URL(`${PHLO_API_URL}${endpoint}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const response = await fetch(url.toString(), {
    method,
    headers:
      body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(timeoutMs),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`phlo-api error: ${response.status} ${text}`)
  }

  return response.json()
}

/**
 * Make a GET request to phlo-api
 */
export async function apiGet<T>(
  endpoint: string,
  params?: Record<string, string | number | boolean | undefined>,
  timeoutMs = 30000,
): Promise<T> {
  return request<T>(endpoint, { params, timeoutMs })
}

/**
 * Make a POST request to phlo-api
 */
export async function apiPost<T>(
  endpoint: string,
  body?: unknown,
  timeoutMs = 30000,
): Promise<T> {
  return request<T>(endpoint, { method: 'POST', body, timeoutMs })
}

/**
 * Make a PUT request to phlo-api
 */
export async function apiPut<T>(
  endpoint: string,
  body?: unknown,
  timeoutMs = 30000,
): Promise<T> {
  return request<T>(endpoint, { method: 'PUT', body, timeoutMs })
}
