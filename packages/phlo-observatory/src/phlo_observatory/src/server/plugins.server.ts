/**
 * Plugins Server Functions
 *
 * Server-side functions for plugin discovery via CLI.
 */

import { exec } from 'node:child_process'
import { promisify } from 'node:util'
import { createServerFn } from '@tanstack/react-start'

const execAsync = promisify(exec)
const pluginCommand = process.env.PHLO_PLUGIN_COMMAND ?? 'phlo'
const registryUrl =
  process.env.PHLO_PLUGIN_REGISTRY_URL ?? 'https://registry.phlo.dev/plugins.json'

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

interface RegistryPayload {
  plugins?: Record<string, Omit<PluginInfo, 'name' | 'type'> & { type?: PluginInfo['type'] }>
}

function parseCliOutput(stdout: string): { installed: Array<PluginInfo>; available: Array<PluginInfo> } {
  const parsed = JSON.parse(stdout)
  if (Array.isArray(parsed)) {
    return { installed: parsed as Array<PluginInfo>, available: [] }
  }
  return {
    installed: parsed.installed ?? [],
    available: parsed.available ?? [],
  }
}

async function fetchRegistryPlugins(): Promise<Array<PluginInfo>> {
  const response = await fetch(registryUrl)
  if (!response.ok) {
    throw new Error(`Registry request failed: ${response.status}`)
  }
  const payload = (await response.json()) as RegistryPayload
  const entries = payload.plugins ?? {}
  return Object.entries(entries).map(([name, info]) => ({
    name,
    type: info.type ?? 'service',
    version: info.version ?? 'unknown',
    description: info.description,
    author: info.author,
    homepage: info.homepage,
    tags: info.tags,
    verified: info.verified,
    core: info.core,
    package: info.package,
  }))
}

async function getPluginLists(): Promise<{
  installed: Array<PluginInfo>
  available: Array<PluginInfo>
}> {
  try {
    const { stdout } = await execAsync(`${pluginCommand} plugin list --all --json`)
    return parseCliOutput(stdout)
  } catch (error) {
    const available = await fetchRegistryPlugins()
    return { installed: [], available }
  }
}

export const getPlugins = createServerFn().handler(
  async (): Promise<Array<PluginInfo>> => {
    const lists = await getPluginLists()
    return lists.installed
  },
)

export const getAvailablePlugins = createServerFn().handler(
  async (): Promise<{ installed: Array<PluginInfo>; available: Array<PluginInfo> }> => {
    return getPluginLists()
  },
)
