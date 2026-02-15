import { describe, expect, it, vi } from 'vitest'

import { resolvePluginLists } from './plugins.server'
import type { PluginInfo } from './plugins.server'

function plugin(
  partial: Partial<PluginInfo> & Pick<PluginInfo, 'name' | 'type' | 'version'>,
): PluginInfo {
  return {
    name: partial.name,
    type: partial.type,
    version: partial.version,
    description: partial.description,
    author: partial.author,
    homepage: partial.homepage,
    tags: partial.tags,
    installed: partial.installed,
    verified: partial.verified,
    core: partial.core,
    package: partial.package,
    category: partial.category,
    profile: partial.profile,
    default: partial.default,
  }
}

describe('plugins.server resolvePluginLists', () => {
  it('uses CLI result when available plugins are present', async () => {
    const runPluginListCommand = vi.fn().mockResolvedValue(
      JSON.stringify({
        installed: [
          plugin({
            name: 'phlo-observatory',
            type: 'service',
            version: '0.1.0',
          }),
        ],
        available: [
          plugin({ name: 'phlo-dlt', type: 'source', version: '0.1.0' }),
        ],
      }),
    )
    const fetchRegistry = vi.fn()

    const result = await resolvePluginLists({
      runPluginListCommand,
      fetchRegistry,
    })

    expect(result.installed).toHaveLength(1)
    expect(result.available).toHaveLength(1)
    expect(fetchRegistry).not.toHaveBeenCalled()
  })

  it('fills available plugins from registry when CLI returns installed only', async () => {
    const runPluginListCommand = vi.fn().mockResolvedValue(
      JSON.stringify({
        installed: [
          plugin({
            name: 'phlo-observatory',
            type: 'service',
            version: '0.1.0',
          }),
        ],
        available: [],
      }),
    )
    const fetchRegistry = vi
      .fn()
      .mockResolvedValue([
        plugin({ name: 'phlo-dbt', type: 'transform', version: '0.1.0' }),
      ])

    const result = await resolvePluginLists({
      runPluginListCommand,
      fetchRegistry,
    })

    expect(result.installed).toHaveLength(1)
    expect(result.available).toHaveLength(1)
    expect(fetchRegistry).toHaveBeenCalledTimes(1)
  })

  it('falls back to registry when CLI command fails', async () => {
    const runPluginListCommand = vi
      .fn()
      .mockRejectedValue(new Error('phlo not found'))
    const fetchRegistry = vi
      .fn()
      .mockResolvedValue([
        plugin({ name: 'phlo-quality', type: 'quality', version: '0.1.0' }),
      ])

    const result = await resolvePluginLists({
      runPluginListCommand,
      fetchRegistry,
    })

    expect(result.installed).toEqual([])
    expect(result.available).toHaveLength(1)
    expect(fetchRegistry).toHaveBeenCalledTimes(1)
  })

  it('returns empty lists when both CLI and registry fail', async () => {
    const runPluginListCommand = vi
      .fn()
      .mockRejectedValue(new Error('phlo not found'))
    const fetchRegistry = vi
      .fn()
      .mockRejectedValue(new Error('registry unavailable'))

    const result = await resolvePluginLists({
      runPluginListCommand,
      fetchRegistry,
    })

    expect(result.installed).toEqual([])
    expect(result.available).toEqual([])
  })
})
