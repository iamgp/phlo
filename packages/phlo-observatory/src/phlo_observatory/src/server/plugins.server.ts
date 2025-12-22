/**
 * Plugins Server Functions
 *
 * Server-side functions for plugin discovery via CLI.
 */

import { exec } from 'node:child_process'
import { promisify } from 'node:util'
import { createServerFn } from '@tanstack/react-start'

const execAsync = promisify(exec)

export interface PluginInfo {
  name: string
  type: 'source' | 'quality' | 'transform' | 'service'
  version: string
  description?: string
  author?: string
  homepage?: string
  tags?: Array<string>
  installed?: boolean
  verified?: boolean
  core?: boolean
  package?: string
  category?: string
  profile?: string | null
  default?: boolean
}

export const getPlugins = createServerFn().handler(
  async (): Promise<Array<PluginInfo>> => {
    const { stdout } = await execAsync('phlo plugin list --json')
    const parsed = JSON.parse(stdout)
    if (Array.isArray(parsed)) {
      return parsed as Array<PluginInfo>
    }
    return parsed.installed ?? []
  },
)

export const getAvailablePlugins = createServerFn().handler(
  async (): Promise<{ installed: Array<PluginInfo>; available: Array<PluginInfo> }> => {
    const { stdout } = await execAsync('phlo plugin list --all --json')
    const parsed = JSON.parse(stdout)
    if (Array.isArray(parsed)) {
      return { installed: parsed as Array<PluginInfo>, available: [] }
    }
    return {
      installed: parsed.installed ?? [],
      available: parsed.available ?? [],
    }
  },
)
