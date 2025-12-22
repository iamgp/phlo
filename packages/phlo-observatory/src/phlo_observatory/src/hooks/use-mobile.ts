import { useEffect, useState } from 'react'

const mobileBreakpointPx = 768

export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return window.innerWidth < mobileBreakpointPx
  })

  useEffect(() => {
    const mediaQuery = window.matchMedia(
      `(max-width: ${mobileBreakpointPx - 1}px)`,
    )

    const onChange = () => {
      setIsMobile(window.innerWidth < mobileBreakpointPx)
    }

    onChange()
    mediaQuery.addEventListener('change', onChange)
    return () => mediaQuery.removeEventListener('change', onChange)
  }, [])

  return isMobile
}
