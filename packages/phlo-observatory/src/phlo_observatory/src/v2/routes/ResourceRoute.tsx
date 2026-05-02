import { useEffect, useState } from 'react'

import type { V2ResourceItem, V2ResourceResult } from '@/v2/api/types'
import { V2EmptyPanel, V2Page, V2ResourcePanel } from '@/v2/components/V2Page'

export interface ResourceRouteConfig {
  kicker: string
  title: string
  description: string
  panelTitle: string
  countLabel: string
  load: () => Promise<V2ResourceResult<Array<V2ResourceItem>>>
  emptyTitle?: string
  emptyBody?: string
  asideTitle: string
  asideBody: string
}

export function ResourceRoute(config: ResourceRouteConfig) {
  const [result, setResult] = useState<V2ResourceResult<Array<V2ResourceItem>>>(
    {
      data: null,
      error: null,
    },
  )

  useEffect(() => {
    let cancelled = false

    async function load() {
      const next = await config.load()
      if (!cancelled) setResult(next)
    }

    void load()
    const interval = window.setInterval(load, 15_000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [config])

  return (
    <V2Page
      kicker={config.kicker}
      title={config.title}
      description={config.description}
    >
      <section className="phlo-v2-split">
        <V2ResourcePanel
          title={config.panelTitle}
          label={config.countLabel}
          result={result}
          emptyTitle={config.emptyTitle}
          emptyBody={config.emptyBody}
        />
        <aside>
          <V2EmptyPanel title={config.asideTitle} body={config.asideBody} />
        </aside>
      </section>
    </V2Page>
  )
}
