// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'

import { QualityDashboardContent } from '@/routes/quality/index'

const invalidateMock = vi.fn()

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router')
  return {
    ...actual,
    Link: ({ children }: { children: ReactNode }) => <span>{children}</span>,
    useRouter: () => ({ invalidate: invalidateMock }),
  }
})

vi.mock('@/hooks/useObservatorySettings', () => ({
  useObservatorySettings: () => ({
    settings: { ui: { dateFormat: 'iso' } },
  }),
}))

vi.mock('@/utils/dateFormat', () => ({
  formatDate: () => '2026-01-01',
  formatDateTime: () => '2026-01-01T00:00:00Z',
}))

describe('quality route dashboard states', () => {
  beforeEach(() => {
    cleanup()
    invalidateMock.mockClear()
  })

  it('renders error state and transitions when error payload changes', () => {
    const { rerender } = render(
      <QualityDashboardContent data={{ error: 'Dagster unavailable' }} />,
    )

    expect(screen.queryByText('Unable to load quality data')).not.toBeNull()
    expect(screen.queryByText('Dagster unavailable')).not.toBeNull()

    rerender(<QualityDashboardContent data={{ error: 'GraphQL timeout' }} />)

    expect(screen.queryByText('Dagster unavailable')).toBeNull()
    expect(screen.queryByText('GraphQL timeout')).not.toBeNull()
  })

  it('triggers router invalidation from the route refresh action', () => {
    render(<QualityDashboardContent data={{ error: 'Dagster unavailable' }} />)

    fireEvent.click(screen.getAllByRole('button', { name: /refresh/i })[0])

    expect(invalidateMock).toHaveBeenCalledTimes(1)
  })
})
