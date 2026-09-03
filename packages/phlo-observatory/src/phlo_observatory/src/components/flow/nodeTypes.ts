/**
 * Shared React Flow node types for journey visualizations.
 */
import { JourneyNode } from './JourneyNode'

export type { JourneyNodeData } from './JourneyNode'

export const journeyNodeTypes = {
  journey: JourneyNode,
} as const
