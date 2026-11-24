import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { RecipeDetail } from '../api/types'
import { Icon } from '../components/Icon'
import { IngredientGroups } from '../components/Ingredients'
import { ErrorState, Spinner } from '../components/States'
import { useFetch } from '../lib/useFetch'
import { useWakeLock } from '../lib/wakeLock'

function useStored<T>(key: string, initial: T) {
  const [v, setV] = useState<T>(() => {
    try {
      const raw = sessionStorage.getItem(key)
      return raw ? (JSON.parse(raw) as T) : initial
    } catch {
      return initial
    }
  })
  useEffect(() => {
    try { sessionStorage.setItem(key, JSON.stringify(v)) } catch { /* private mode */ }
  }, [key, v])
  return [v, setV] as const
}

export function CookPage() {
  const { slug = '' } = useParams()
  const [params] = useSearchParams()
  const servings = params.get('servings') ? Number(params.get('servings')) : undefined
  const recipe = useFetch<RecipeDetail>(() => api.recipe(slug, servings), `${slug}:${servings}`)
  const wake = useWakeLock(true)

  const [step, setStep] = useStored(`cook:${slug}:step`, 0)
  const [checkedArr, setCheckedArr] = useStored<number[]>(`cook:${slug}:checked`, [])
  const checked = new Set(checkedArr)
  const [sheet, setSheet] = useState(false)
  const sheetRef = useRef<HTMLDialogElement>(null)
  const stepRef = useRef<HTMLDivElement>(null)

  const r = recipe.data
  const total = r?.steps.length ?? 0
  const done = step >= total && total > 0

  const go = useCallback((d: number) => setStep((s) => Math.max(0, Math.min(total, s + d))), [setStep, total])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (sheet) return
      if ((e.target as HTMLElement).closest('input, textarea, select')) return
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || (e.key === ' ' && !(e.target as HTMLElement).closest('button, a'))) { e.preventDefault(); go(1) }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); go(-1) }
      else if (e.key.toLowerCase() === 'i') { e.preventDefault(); setSheet(true) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, sheet])

  useEffect(() => {
    const d = sheetRef.current
    if (!d) return
    if (sheet && !d.open) d.showModal()
    if (!sheet && d.open) d.close()
  }, [sheet])

  // Move focus to the step text so screen readers announce it.
  useEffect(() => { stepRef.current?.focus({ preventScroll: true }) }, [step])

  // Swipe left/right on the step.
  const touch = useRef<{ x: number; y: number } | null>(null)
  const onTouchStart = (e: React.TouchEvent) => { touch.current = { x: e.touches[0].clientX, y: e.touches[0].clientY } }
  const onTouchEnd = (e: React.TouchEvent) => {
    if (!touch.current) return
    const dx = e.changedTouches[0].clientX - touch.current.x
    const dy = e.changedTouches[0].clientY - touch.current.y
    touch.current = null
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) go(dx < 0 ? 1 : -1)
  }

  if (recipe.error) return <div className="cook"><ErrorState error={recipe.error} onRetry={recipe.reload} /></div>
  if (!r) return <div className="cook cook-loading"><Spinner /></div>

  const back = `/r/${r.slug}${servings ? `?servings=${servings}` : ''}`
  const itemCount = r.groups.flatMap((g) => g.items).filter((i) => i.kind === 'item').length
  const toggle = (id: number) => setCheckedArr((a) => (a.includes(id) ? a.filter((x) => x !== id) : [...a, id]))

  return (
    <div className="cook">
      <header className="cook-top">
        <Link to={back} className="btn btn-icon btn-ghost" aria-label="Exit cook mode">
          <Icon name="close" size={24} />
        </Link>
        <div className="cook-title">
          <p>{r.title}</p>
          <p className="cook-sub">
            {r.scaled_servings ? `${r.scaled_servings} servings` : null}
            <span className={`wake wake-${wake}`}>
              {wake === 'on' ? 'Screen stays on' : wake === 'unsupported' ? 'Screen may dim (keep-awake not supported here)' : 'Screen may dim'}
            </span>
          </p>
        </div>
        <button type="button" className="btn cook-ing-btn" onClick={() => setSheet(true)} aria-haspopup="dialog">
          <Icon name="list" size={20} /> <span className="hide-sm">Ingredients</span>
          <span className="count">{checked.size}/{itemCount}</span>
        </button>
      </header>

      <div className="cook-progress" role="progressbar" aria-valuemin={1} aria-valuemax={total} aria-valuenow={Math.min(step + 1, total)} aria-label="Step progress">
        {r.steps.map((_, i) => (
          <button
            key={i}
            type="button"
            className={`cook-seg${i < step ? ' is-done' : ''}${i === step ? ' is-now' : ''}`}
            onClick={() => setStep(i)}
            aria-label={`Go to step ${i + 1}`}
          />
        ))}
      </div>

      <main className="cook-main" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
        {total === 0 ? (
          <div className="cook-step"><p className="cook-text">This recipe has no steps yet.</p></div>
        ) : done ? (
          <div className="cook-step cook-done" ref={stepRef} tabIndex={-1}>
            <p className="cook-count">Done</p>
            <p className="cook-text">That's everything. Portion it up while it's warm, then let it cool before it goes in the fridge.</p>
            {r.notes.length > 0 && (
              <div className="tips">
                <h2>Tips</h2>
                <ul>{r.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
              </div>
            )}
          </div>
        ) : (
          <div className="cook-step" ref={stepRef} tabIndex={-1} aria-live="polite" key={step}>
            <p className="cook-count">Step {step + 1} <span>of {total}</span></p>
            <p className="cook-text">{r.steps[step]}</p>
          </div>
        )}
      </main>

      <nav className="cook-nav" aria-label="Steps">
        <button type="button" className="btn btn-xl" onClick={() => go(-1)} disabled={step === 0}>
          <Icon name="back" size={26} /> Back
        </button>
        {done ? (
          <Link to={back} className="btn btn-xl btn-primary">Finish</Link>
        ) : (
          <button type="button" className="btn btn-xl btn-primary" onClick={() => go(1)} disabled={total === 0}>
            {step === total - 1 ? 'Last step done' : 'Next'} <Icon name="forward" size={26} />
          </button>
        )}
      </nav>

      <dialog ref={sheetRef} className="sheet" onClose={() => setSheet(false)} onClick={(e) => { if (e.target === e.currentTarget) setSheet(false) }} aria-labelledby="sheet-h">
        <div className="sheet-inner">
          <div className="sheet-head">
            <h2 id="sheet-h">Ingredients{r.scaled_servings ? <span> · {r.scaled_servings} servings</span> : null}</h2>
            <button type="button" className="btn btn-icon btn-ghost" onClick={() => setSheet(false)} aria-label="Close ingredients">
              <Icon name="close" size={24} />
            </button>
          </div>
          <div className="sheet-body">
            <IngredientGroups groups={r.groups} checked={checked} onToggle={toggle} />
            {checked.size > 0 && (
              <button type="button" className="linkbtn" onClick={() => setCheckedArr([])}>Clear ticks</button>
            )}
          </div>
        </div>
      </dialog>
    </div>
  )
}
