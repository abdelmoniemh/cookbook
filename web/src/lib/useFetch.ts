import { useCallback, useEffect, useRef, useState } from 'react'

export type FetchState<T> = {
  data: T | undefined
  error: Error | undefined
  loading: boolean
  reload: () => void
  setData: (updater: T | ((prev: T | undefined) => T | undefined)) => void
}

/** Runs `fn` whenever `key` changes. Keeps the previous data while a new request is in flight. */
export function useFetch<T>(fn: () => Promise<T>, key: string): FetchState<T> {
  const [data, setDataState] = useState<T>()
  const [error, setError] = useState<Error>()
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let live = true
    setLoading(true)
    setError(undefined)
    fnRef.current().then(
      (d) => { if (live) { setDataState(d); setLoading(false) } },
      (e: Error) => { if (live) { setError(e); setLoading(false) } },
    )
    return () => { live = false }
  }, [key, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  const setData = useCallback((u: T | ((prev: T | undefined) => T | undefined)) => {
    setDataState((prev) => (typeof u === 'function' ? (u as (p: T | undefined) => T | undefined)(prev) : u))
  }, [])
  return { data, error, loading, reload, setData }
}
