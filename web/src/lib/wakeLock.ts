import { useEffect, useState } from 'react'

export type WakeState = 'on' | 'off' | 'unsupported'

/** Keeps the screen awake while mounted. Re-acquires the lock when the tab becomes visible again. */
export function useWakeLock(enabled = true): WakeState {
  const supported = typeof navigator !== 'undefined' && 'wakeLock' in navigator
  const [state, setState] = useState<WakeState>(supported ? 'off' : 'unsupported')

  useEffect(() => {
    if (!supported || !enabled) return
    let sentinel: WakeLockSentinel | null = null
    let cancelled = false
    const acquire = async () => {
      try {
        sentinel = await navigator.wakeLock.request('screen')
        if (cancelled) { sentinel.release(); return }
        setState('on')
        sentinel.addEventListener('release', () => { if (!cancelled) setState('off') })
      } catch {
        setState('off')
      }
    }
    const onVisible = () => { if (document.visibilityState === 'visible') acquire() }
    acquire()
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisible)
      sentinel?.release().catch(() => {})
    }
  }, [supported, enabled])

  return state
}
