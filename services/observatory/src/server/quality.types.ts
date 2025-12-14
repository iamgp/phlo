export type MetadataValue = string | number | boolean | null | undefined

export interface QualityCheck {
  name: string
  assetKey: Array<string>
  description?: string
  severity: 'ERROR' | 'WARN'
  status: 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS'
  lastExecutionTime?: string
  lastResult?: {
    passed: boolean
    metadata?: Record<string, MetadataValue>
  }
}

export interface QualityOverview {
  totalChecks: number
  passingChecks: number
  failingChecks: number
  warningChecks: number
  qualityScore: number // 0-100 percentage
  byCategory: Array<{
    category: string
    passing: number
    total: number
    percentage: number
  }>
  trend: Array<{
    date: string
    score: number
  }>
}

export interface CheckExecution {
  timestamp: string
  passed: boolean
  runId?: string
  metadata?: Record<string, MetadataValue>
}

export interface RecentCheckExecution extends CheckExecution {
  assetKey: Array<string>
  checkName: string
  status: 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS'
  severity: 'ERROR' | 'WARN'
}
