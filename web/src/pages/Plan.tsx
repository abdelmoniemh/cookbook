import { useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Day, Plan, PlanEntry } from '../api/types'
import { PageHeader } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { MacroBar } from '../components/MacroBar'
import { Photo } from '../components/Photo'
import { EmptyState, ErrorState, Spinner } from '../components/States'
import { Stepper } from '../components/Stepper'
import { num } from '../lib/format'
import { useToast } from '../lib/toast'
import { useFetch } from '../lib/useFetch'
import { DAYS, mondayOf, relativeWeek, shiftWeek, weekLabel } from '../lib/week'

export function PlanPage() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const week = params.get('week') ?? mondayOf()
  const isThisWeek = week === mondayOf()
  const plan = useFetch<Plan>(() => api.currentPlan(week), week)
  const timers = useRef(new Map<number, number>())

  useEffect(() => () => timers.current.forEach((t) => window.clearTimeout(t)), [])

  function goWeek(delta: number) {
    const next = shiftWeek(week, delta)
    setParams(next === mondayOf() ? {} : { week: next }, { replace: true })
  }

  const p = plan.data
  const weekQs = isThisWeek ? '' : `?week=${week}`

  function recalc(entries: PlanEntry[]): Plan['totals'] {
    const t = { servings: 0, kcal: 0, protein: 0, carbs: 0, fat: 0 }
    for (const e of entries) {
      t.servings += e.servings
      t.kcal += (e.recipe.kcal ?? 0) * e.servings
      t.protein += (e.recipe.protein ?? 0) * e.servings
      t.carbs += (e.recipe.carbs ?? 0) * e.servings
      t.fat += (e.recipe.fat ?? 0) * e.servings
    }
    return t
  }

  function patchLocal(entryId: number, change: Partial<PlanEntry>) {
    plan.setData((d) => {
      if (!d) return d!
      const entries = d.entries.map((e) => (e.id === entryId ? { ...e, ...change } : e))
      return { ...d, entries, totals: recalc(entries) }
    })
  }

  function setServings(e: PlanEntry, n: number) {
    if (!p) return
    patchLocal(e.id, { servings: n })
    const prev = timers.current.get(e.id)
    if (prev) window.clearTimeout(prev)
    timers.current.set(e.id, window.setTimeout(async () => {
      try {
        plan.setData(await api.updateEntry(p.id, e.id, { servings: n }))
      } catch (err) {
        toast({ text: `Couldn't save servings: ${(err as Error).message}`, tone: 'error' })
        plan.reload()
      }
    }, 400))
  }

  async function setDay(e: PlanEntry, day: Day | null) {
    if (!p) return
    patchLocal(e.id, { day })
    try {
      plan.setData(await api.updateEntry(p.id, e.id, { day }))
    } catch (err) {
      toast({ text: `Couldn't move it: ${(err as Error).message}`, tone: 'error' })
      plan.reload()
    }
  }

  async function remove(e: PlanEntry) {
    if (!p) return
    const before = p
    plan.setData((d) => {
      const entries = d!.entries.filter((x) => x.id !== e.id)
      return { ...d!, entries, totals: recalc(entries) }
    })
    try {
      plan.setData(await api.removeEntry(p.id, e.id))
      toast({ text: `Removed ${e.recipe.title}` })
    } catch (err) {
      plan.setData(before)
      toast({ text: `Couldn't remove: ${(err as Error).message}`, tone: 'error' })
    }
  }

  const groups: { key: string; label: string; entries: PlanEntry[] }[] = []
  if (p) {
    const anytime = p.entries.filter((e) => !e.day)
    if (anytime.length) groups.push({ key: 'any', label: 'Any day', entries: anytime })
    for (const d of DAYS) {
      const es = p.entries.filter((e) => e.day === d.id)
      if (es.length) groups.push({ key: d.id, label: d.long, entries: es })
    }
  }
  const t = p?.totals
  const perServing = t && t.servings ? { kcal: t.kcal / t.servings, protein: t.protein / t.servings, carbs: t.carbs / t.servings, fat: t.fat / t.servings } : null

  return (
    <div className="plan">
      <PageHeader
        title="Plan"
        sub={
          <span className="weeknav">
            <button type="button" className="btn btn-icon btn-ghost" onClick={() => goWeek(-1)} aria-label="Previous week"><Icon name="back" size={20} /></button>
            <span className="weeknav-label"><strong>{relativeWeek(week)}</strong> {weekLabel(week)}</span>
            <button type="button" className="btn btn-icon btn-ghost" onClick={() => goWeek(1)} aria-label="Next week"><Icon name="forward" size={20} /></button>
            {!isThisWeek && <button type="button" className="linkbtn" onClick={() => setParams({}, { replace: true })}>Back to this week</button>}
          </span>
        }
        actions={
          <>
            <Link className="btn" to={`/?add=1${isThisWeek ? '' : `&week=${week}`}`}><Icon name="plus" size={18} /> Add recipes</Link>
            <Link className="btn btn-primary" to={`/shopping${weekQs}`}><Icon name="basket" size={18} /> Shopping list</Link>
          </>
        }
      />

      {plan.error ? (
        <ErrorState error={plan.error} onRetry={plan.reload} />
      ) : !p ? (
        <div className="state"><Spinner /></div>
      ) : p.entries.length === 0 ? (
        <EmptyState
          title="Nothing planned yet"
          action={<Link className="btn btn-primary" to={`/?add=1${isThisWeek ? '' : `&week=${week}`}`}><Icon name="plus" size={18} /> Pick recipes</Link>}
        >
          <p>Pick a couple of meal preps for the batch cook, and any breakfasts or snacks. The shopping list builds itself from this plan.</p>
        </EmptyState>
      ) : (
        <div className="plan-layout">
          <section className="plan-totals" aria-labelledby="totals-h">
            <h2 id="totals-h">Week total</h2>
            <p className="plan-big">
              <span><strong>{num(t!.protein)}</strong><span className="unit">g</span> <span className="lbl">protein</span></span>
              <span><strong>{num(t!.kcal)}</strong> <span className="lbl">kcal</span></span>
            </p>
            <MacroBar protein={t!.protein} carbs={t!.carbs} fat={t!.fat} size="md" />
            <dl className="plan-table">
              <div><dt>Servings</dt><dd>{num(t!.servings, 1)}</dd></div>
              <div><dt>Carbs</dt><dd>{num(t!.carbs)} g</dd></div>
              <div><dt>Fat</dt><dd>{num(t!.fat)} g</dd></div>
            </dl>
            {perServing && (
              <>
                <h3>Average serving</h3>
                <dl className="plan-table">
                  <div><dt>kcal</dt><dd>{num(perServing.kcal)}</dd></div>
                  <div><dt>Protein</dt><dd>{num(perServing.protein)} g</dd></div>
                  <div><dt>Carbs</dt><dd>{num(perServing.carbs)} g</dd></div>
                  <div><dt>Fat</dt><dd>{num(perServing.fat)} g</dd></div>
                </dl>
              </>
            )}
          </section>

          <div className="plan-entries">
            {groups.map((g) => (
              <section key={g.key} className="plan-day" aria-label={g.label}>
                <h2 className="plan-day-h">{g.label}</h2>
                <ul>
                  {g.entries.map((e) => (
                    <li key={e.id} className="entry">
                      <Link to={`/r/${e.recipe.slug}?servings=${e.servings}`} className="entry-photo" tabIndex={-1} aria-hidden="true">
                        <Photo src={e.recipe.image_url} alt="" />
                      </Link>
                      <div className="entry-main">
                        <Link to={`/r/${e.recipe.slug}?servings=${e.servings}`} className="entry-title">{e.recipe.title}</Link>
                        <p className="entry-macros">
                          <span className="m-protein">{num(e.recipe.protein)}g protein</span> · {num(e.recipe.kcal)} kcal per serving
                        </p>
                      </div>
                      <div className="entry-controls">
                        <Stepper label="Servings" value={e.servings} onChange={(n) => setServings(e, n)} suffix={e.servings === 1 ? 'serving' : 'servings'} />
                        <label className="select select-compact">
                          <span className="sr-only">Day for {e.recipe.title}</span>
                          <select value={e.day ?? ''} onChange={(ev) => setDay(e, (ev.target.value || null) as Day | null)}>
                            <option value="">Any day</option>
                            {DAYS.map((d) => <option key={d.id} value={d.id}>{d.short}</option>)}
                          </select>
                        </label>
                        <button type="button" className="btn btn-icon btn-ghost" onClick={() => remove(e)} aria-label={`Remove ${e.recipe.title} from plan`}>
                          <Icon name="trash" size={20} />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
