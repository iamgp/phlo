/**
 * Structured Logging with Pino
 *
 * Provides structured JSON logging for Observatory server functions.
 * Logs are collected by Grafana Alloy and stored in Loki.
 */

import pino from 'pino'

const logger = pino({
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
