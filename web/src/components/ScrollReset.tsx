import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Scroll to top on path changes (not on query changes, so filters keep your place). */
export function ScrollReset() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}
