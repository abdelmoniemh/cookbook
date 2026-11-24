import { useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { ShoppingItem, ShoppingList } from '../api/types'
import { PageHeader } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { EmptyState, ErrorState, Spinner } from '../components/States'
import { useToast } from '../lib/toast'
import { useFetch } from '../lib/useFetch'
import { mondayOf, relativeWeek, weekLabel } from '../lib/week'

const PANTRY_AISLE = 'Spices & Seasonings'

type Loaded = { list: ShoppingList; week: string; entries: number }

export function ShoppingPage() {
  const [params] = useSearchParams()
  const toast = useToast()
  const week = params.get('week') ?? undefined
  const state = useFetch<Loaded>(async () => {
    const plan = await api.currentPlan(week)
    return { list: await api.shopping(plan.id), week: plan.week_start, entries: plan.entries.length }
  }, week ?? 'now')
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [extra, setExtra] = useState('')
  const [adding, setAdding] = useState(false)
  // Checks the server hasn't confirmed yet; laid over every response so quick taps never flicker back.
  const pending = useRef(new Map<string, boolean>())

  const data = state.data
  const withPending = (list: ShoppingList): ShoppingList => ({
    ...list,
    aisles: list.aisles.map((a) => ({ ...a, items: a.items.map((i) => (pending.current.has(i.key) ? { ...i, checked: pending.current.get(i.key)! } : i)) })),
  })
  const setList = (list: ShoppingList) => state.setData((d) => ({ ...d!, list: withPending(list) }))

  async function toggle(item: ShoppingItem) {
    if (!data) return
    const next = !item.checked
    pending.current.set(item.key, next)
    setList(data.list)
    try {
      const res = await api.setChecked(data.list.plan_id, item.key, next)
      if (pending.current.get(item.key) === next) pending.current.delete(item.key)
      setList(res)
    } catch (e) {
      pending.current.delete(item.key)
      state.setData((d) => ({ ...d!, list: { ...d!.list, aisles: d!.list.aisles.map((a) => ({ ...a, items: a.items.map((i) => (i.key === item.key ? { ...i, checked: item.checked } : i)) })) } }))
      toast({ text: `Couldn't save that tick: ${(e as Error).message}`, tone: 'error' })
    }
  }

  async function addExtra(e: React.FormEvent) {
    e.preventDefault()
    const text = extra.trim()
    if (!text || !data) return
    setAdding(true)
    try {
      setList(await api.addExtra(data.list.plan_id, text))
      setExtra('')
    } catch (err) {
      toast({ text: `Couldn't add “${text}”: ${(err as Error).message}`, tone: 'error' })
    } finally {
      setAdding(false)
    }
  }

  async function removeExtra(item: ShoppingItem) {
    if (!data) return
    try {
      setList(await api.removeExtra(data.list.plan_id, item.key.replace(/^extra:/, '')))
    } catch (err) {
      toast({ text: `Couldn't remove it: ${(err as Error).message}`, tone: 'error' })
    }
  }

  const all = data?.list.aisles.flatMap((a) => a.items) ?? []
  const doneCount = all.filter((i) => i.checked).length
  const isOpen = (aisle: string) => open[aisle] ?? aisle !== PANTRY_AISLE
  const planHref = data && data.week !== mondayOf() ? `/plan?week=${data.week}` : '/plan'

  return (
    <div className="shopping">
      <PageHeader
        title="Shopping"
        sub={data ? <>{relativeWeek(data.week)} {weekLabel(data.week)} · {data.entries ? <Link to={planHref}>{data.entries} {data.entries === 1 ? 'recipe' : 'recipes'}</Link> : 'nothing planned'}</> : null}
      />

      {state.error ? (
        <ErrorState error={state.error} onRetry={state.reload} />
      ) : !data ? (
        <div className="state"><Spinner /></div>
      ) : data.entries === 0 && all.length === 0 ? (
        <EmptyState title="Your list is empty" action={<Link className="btn btn-primary" to={planHref}><Icon name="plan" size={18} /> Plan the week</Link>}>
          <p>The shopping list builds itself from the recipes in this week's plan, merged and grouped by aisle.</p>
        </EmptyState>
      ) : (
        <>
          <div className="shop-progress" aria-live="polite">
            {all.length > 0 && doneCount === all.length ? (
              <p className="shop-done"><Icon name="check" size={18} /> Everything's in the basket. Enjoy the cook.</p>
            ) : (
              <p><strong>{doneCount}</strong> of {all.length} in the basket</p>
            )}
            <div className="shop-meter" aria-hidden="true"><span style={{ width: `${all.length ? (doneCount / all.length) * 100 : 0}%` }} /></div>
          </div>

          {data.list.aisles.map((a) => {
            const left = a.items.filter((i) => !i.checked).length
            const sorted = [...a.items].sort((x, y) => Number(x.checked) - Number(y.checked))
            const expanded = isOpen(a.aisle)
            const id = `aisle-${a.aisle.replace(/\W+/g, '-')}`
            return (
              <section key={a.aisle} className={`aisle${left === 0 ? ' is-done' : ''}`} aria-labelledby={`${id}-h`}>
                <h2 id={`${id}-h`} className="aisle-h">
                  <button type="button" aria-expanded={expanded} aria-controls={id} onClick={() => setOpen((o) => ({ ...o, [a.aisle]: !expanded }))}>
                    <span className="aisle-name">{a.aisle}</span>
                    <span className="aisle-left">{left === 0 ? <><Icon name="check" size={16} /> done</> : `${left} left`}</span>
                    <Icon name="chevronDown" size={20} className="aisle-chev" />
                  </button>
                </h2>
                {a.aisle === PANTRY_AISLE && !expanded && left > 0 && <p className="aisle-hint">Check the cupboard first: you probably have most of these.</p>}
                {expanded && (
                  <ul id={id} className="shop-list">
                    {sorted.map((item) => (
                      <li key={item.key} className={item.checked ? 'is-checked' : ''}>
                        <button type="button" role="checkbox" aria-checked={item.checked} className="shop-item" onClick={() => toggle(item)}>
                          <span className="tick" aria-hidden="true"><Icon name="check" size={18} /></span>
                          <span className="shop-text">
                            <span className="shop-name">{item.name}</span>
                            {item.recipes.length > 0 && <span className="shop-recipes">{item.recipes.join(' · ')}</span>}
                          </span>
                          {item.display && <span className={`shop-qty${item.display === 'as needed' ? ' is-vague' : ''}`}>{item.display}</span>}
                        </button>
                        {item.extra && (
                          <button type="button" className="btn btn-icon btn-ghost shop-remove" onClick={() => removeExtra(item)} aria-label={`Remove ${item.name}`}>
                            <Icon name="close" size={18} />
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )
          })}

          <form className="extra-form" onSubmit={addExtra}>
            <label htmlFor="extra-input">Add something else</label>
            <div className="extra-row">
              <input id="extra-input" type="text" placeholder="Bin bags, coffee…" value={extra} onChange={(e) => setExtra(e.target.value)} enterKeyHint="done" autoComplete="off" />
              <button type="submit" className="btn btn-primary" disabled={!extra.trim() || adding}>
                {adding ? <Spinner label="Adding" /> : <Icon name="plus" size={18} />} Add
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}
