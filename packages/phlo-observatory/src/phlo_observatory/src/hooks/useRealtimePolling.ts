/**
 * Real-time polling hook for Observatory
 *
 * ADR: 0026-observatory-auth-and-realtime.md
 * Bead: phlo-cil
 *
 * Provides automatic polling for live data updates using TanStack Query.
 */

import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query'

import { useObservatorySettings } from '@/hooks/useObservatorySettings'

/**
 * Default polling interval when not configured
 */
const DEFAULT_INTERVAL_MS = 5000

/**
 * Hook for real-time data polling
 *
 * Uses TanStack Query's refetchInterval with settings from ObservatorySettings.
 * Polling is automatically paused when the tab is in the background.
 *
 * @param options - TanStack Query options (queryKey, queryFn required)
 * @returns TanStack Query result with automatic polling
 *
 * @example
 * ```tsx
 * const { data, isLoading, dataUpdatedAt } = useRealtimePolling({
 *   queryKey: ['health-metrics'],
 *   queryFn: () => getHealthMetrics({ data: {} }),
 * })
 * ```
 */
export function useRealtimePolling<
  TQueryFnData = unknown,
  TError = Error,
  TData = TQueryFnData,
>(
  options: UseQueryOptions<TQueryFnData, TError, TData> & {
    /** Override enabled state (in addition to global realtime.enabled) */
    pollingEnabled?: boolean
  },
): UseQueryResult<TData, TError> & {
  /** Whether polling is currently active */
  isPolling: boolean
  /** The current polling interval in ms */
  pollingIntervalMs: number
} {
  const { settings } = useObservatorySettings()

  // Get realtime settings with defaults
  const realtimeEnabled = settings.realtime?.enabled ?? true
  const intervalMs = settings.realtime?.intervalMs ?? DEFAULT_INTERVAL_MS

  // Polling is active if both global and local settings allow it
  const isPolling =
    realtimeEnabled &&
    (options.pollingEnabled ?? true) &&
    options.enabled !== false

  const queryResult = useQuery({
    ...options,
    refetchInterval: isPolling ? intervalMs : false,
    // Don't poll in background to save resources
    refetchIntervalInBackground: false,
  })

  return {
    ...queryResult,
    isPolling,
    pollingIntervalMs: intervalMs,
  }
}

/**
 * Format time since last update for display
 *
 * @param timestamp - Timestamp of last update (ms)
 * @returns Human-readable string like "5s ago" or "2m ago"
 */
export function formatTimeSince(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000)

  if (seconds < 60) {
    return `${seconds}s ago`
  }

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m ago`
  }

  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}
