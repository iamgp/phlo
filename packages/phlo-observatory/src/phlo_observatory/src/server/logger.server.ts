/**
 * Structured Logging with Pino
 *
 * Provides structured JSON logging for Observatory server functions.
 * Logs are collected by Grafana Alloy and stored in Loki.
 */

import pino from 'pino'

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
})

/**
 * Create a child logger with function context
 */
export function fnLogger(fn: string, meta?: Record<string, unknown>) {
  return logger.child({ fn, ...meta })
}

/**
 * Wrap an async operation with timing and structured logging
 *
 * @example
 * return withTiming('previewData', async () => {
 *   // existing logic
 * }, { table, branch })
 */
export async function withTiming<T>(
  fn: string,
  operation: () => Promise<T>,
  meta?: Record<string, unknown>,
): Promise<T> {
  const log = fnLogger(fn, meta)
  const start = performance.now()

  try {
    const result = await operation()
    const durationMs = Math.round(performance.now() - start)
    log.info({ durationMs }, 'completed')
    return result
  } catch (error) {
    const durationMs = Math.round(performance.now() - start)
    log.error({ durationMs, err: error }, 'failed')
    throw error
  }
}

/**
 * Wrap an async operation with timing and budget warning
 *
 * @example
 * return withTimingBudget('listAssets', 2000, async () => {
 *   // existing logic
 * }, { dagsterUrl })
 */
export async function withTimingBudget<T>(
  fn: string,
  budgetMs: number,
  operation: () => Promise<T>,
  meta?: Record<string, unknown>,
): Promise<T> {
  const log = fnLogger(fn, meta)
  const start = performance.now()

  try {
    const result = await operation()
    const durationMs = Math.round(performance.now() - start)

    if (durationMs > budgetMs) {
      log.warn({ durationMs, budgetMs }, 'exceeded budget')
    } else {
      log.info({ durationMs }, 'completed')
    }

    return result
  } catch (error) {
    const durationMs = Math.round(performance.now() - start)
    log.error({ durationMs, err: error }, 'failed')
    throw error
  }
}
