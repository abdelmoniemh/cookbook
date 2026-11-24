import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Plan, RecipeList, RecipeQuery, RecipeSummary } from '../api/types'
import { Icon } from '../components/Icon'
import { RecipeCard } from '../components/RecipeCard'
import { CardSkeletons, EmptyState, ErrorState } from '../components/States'
import { useToast } from '../lib/toast'
import { useFetch } from '../lib/useFetch'
import { relativeWeek, weekLabel } from '../lib/week'

const PAGE = 48
const SORTS: { id: NonNullable<RecipeQuery['sort']>; label: string }[] = [
  { id: 'title', label: 'A–Z' },
  { id: 'protein', label: 'Most protein' },
  { id: 'kcal', label: 'Fewest kcal' },
  { id: 'recent', label: 'Newest' },
]

export function BrowsePage() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const q = params.get('q') ?? ''
  const tags = params.getAll('tag')
  const source = params.get('source') ?? ''
  const fav = params.get('fav') === '1'
  const sort = (params.get('sort') as RecipeQuery['sort']) ?? 'title'
  const addMode = params.get('add') === '1'
  const week = params.get('week') ?? undefined

  const [text, setText] = useState(q)
  useEffect(() => setText(q), [q])
  useEffect(() => {
    if (text === q) return
    const t = window.setTimeout(() => update((p) => (text ? p.set('q', text) : p.delete('q'))), 250)
    return () => window.clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text])

  function update(fn: (p: URLSearchParams) => void) {
    const next = new URLSearchParams(params)
    fn(next)
    setParams(next, { replace: true })
  }

  const [limit, setLimit] = useState(PAGE)
  const queryKey = JSON.stringify({ q, tags, source, fav, sort })
  useEffect(() => setLimit(PAGE), [queryKey])

  const query: RecipeQuery = { q: q || undefined, tag: tags, source: source ? Number(source) : undefined, favourite: fav || undefined, sort, limit }
  const list = useFetch<RecipeList>(() => api.recipes(query), queryKey + limit)
  const tagList = useFetch(() => api.tags(), 'tags')
  const sources = useFetch(() => api.sources(), 'sources')
  const plan = useFetch<Plan | undefined>(() => (addMode ? api.currentPlan(week) : Promise.resolve(undefined)), `plan:${addMode}:${week}`)
  const inPlan = useMemo(() => new Set(plan.data?.entries.map((e) => e.recipe.id)), [plan.data])

  const filtered = Boolean(q || tags.length || source || fav)
  const items = list.data?.items ?? []

  async function toggleFav(r: RecipeSummary) {
    const flip = (on: boolean) => list.setData((d) => d && { ...d, items: d.items.map((x) => (x.id === r.id ? { ...x, favourite: on } : x)) })
    flip(!r.favourite)
    try {
      await api.setFavourite(r.id, !r.favourite)
    } catch (e) {
      flip(r.favourite)
      toast({ text: `Couldn't update favourite: ${(e as Error).message}`, tone: 'error' })
    }
  }

  async function addToPlan(r: RecipeSummary) {
    if (!plan.data) return
    try {
      const next = await api.addEntry(plan.data.id, { recipe_id: r.id, servings: r.servings ?? 1 })
      plan.setData(next)
      toast({ text: `Added ${r.title}`, link: { to: week ? `/plan?week=${week}` : '/plan', label: 'View plan' } })
    } catch (e) {
      toast({ text: `Couldn't add to plan: ${(e as Error).message}`, tone: 'error' })
    }
  }

  function toggleTag(t: string) {
    update((p) => {
      const cur = p.getAll('tag')
      p.delete('tag')
      ;(cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]).forEach((x) => p.append('tag', x))
    })
  }

  // First run: nothing imported at all.
  const noRecipesAtAll = !list.loading && !list.error && !filtered && list.data?.total === 0

  const selects = (
    <>
          {(sources.data?.length ?? 0) > 1 && (
            <label className="select">
              <span className="sr-only">Book</span>
              <Icon name="book" size={18} />
              <select value={source} onChange={(e) => update((p) => (e.target.value ? p.set('source', e.target.value) : p.delete('source')))}>
                <option value="">All books</option>
                {sources.data!.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.recipe_count})</option>
                ))}
              </select>
            </label>
          )}
          <label className="select">
            <span className="sr-only">Sort</span>
            <Icon name="sort" size={18} />
            <select value={sort} onChange={(e) => update((p) => (e.target.value === 'title' ? p.delete('sort') : p.set('sort', e.target.value)))}>
              {SORTS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </label>
    </>
  )

  return (
    <div className="browse">
      {addMode && plan.data && (
        <div className="addbar" role="region" aria-label="Adding to plan">
          <p>
            Adding to <strong>{relativeWeek(plan.data.week_start).toLowerCase()}</strong>
            <span className="addbar-week"> · {weekLabel(plan.data.week_start)}</span>
            <span className="addbar-count"> · {plan.data.entries.length} planned</span>
          </p>
          <Link className="btn btn-on-shell" to={week ? `/plan?week=${week}` : '/plan'}>Done</Link>
        </div>
      )}

      <div className="browse-tools">
        <div className="search">
          <Icon name="search" size={20} />
          <input
            type="search"
            placeholder="Search recipes, ingredients…"
            aria-label="Search recipes"
            value={text}
            onChange={(e) => setText(e.target.value)}
            enterKeyHint="search"
          />
          {text && (
            <button type="button" className="search-clear" aria-label="Clear search" onClick={() => { setText(''); update((p) => p.delete('q')) }}>
              <Icon name="close" size={18} />
            </button>
          )}
        </div>
        <div className="browse-selects only-desktop">{selects}</div>
      </div>

      <div className="chips" role="group" aria-label="Filter">
        <span className="only-phone chip-selects">{selects}</span>
        <button type="button" className={`chip chip-fav${fav ? ' is-on' : ''}`} aria-pressed={fav} onClick={() => update((p) => (fav ? p.delete('fav') : p.set('fav', '1')))}>
          <Icon name="heart" size={16} filled={fav} /> Favourites
        </button>
        {tagList.data?.map((t) => (
          <button key={t.tag} type="button" className={`chip${tags.includes(t.tag) ? ' is-on' : ''}`} aria-pressed={tags.includes(t.tag)} onClick={() => toggleTag(t.tag)}>
            {t.tag}
            <span className="chip-count">{t.count}</span>
          </button>
        ))}
      </div>

      <div className="browse-status" aria-live="polite">
        {list.data && !noRecipesAtAll && (
          <p>
            {list.data.total} {list.data.total === 1 ? 'recipe' : 'recipes'}
            {filtered && (
              <button type="button" className="linkbtn" onClick={() => { setText(''); setParams(addMode ? { add: '1', ...(week ? { week } : {}) } : {}, { replace: true }) }}>
                Clear filters
              </button>
            )}
          </p>
        )}
      </div>

      {list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} />
      ) : noRecipesAtAll ? (
        <EmptyState
          title="No recipes yet"
          action={<><Link className="btn btn-primary" to="/import"><Icon name="upload" size={18} /> Import a cookbook PDF</Link><Link className="btn" to="/new">Write one by hand</Link></>}
        >
          <p>Import your cookbook PDFs from the terminal on the home PC:</p>
          <pre className="code">uv run cookbook-import path/to/Cookbook.pdf</pre>
          <p>or upload a PDF here. Photos, macros and video links come across with each recipe.</p>
        </EmptyState>
      ) : list.data && items.length === 0 && !list.loading ? (
        <EmptyState title="No recipes match" action={<button type="button" className="btn" onClick={() => { setText(''); setParams({}, { replace: true }) }}>Clear filters</button>}>
          <p>Try fewer filters or a different word{q ? <> than “{q}”</> : null}.</p>
        </EmptyState>
      ) : (
        <>
          <div className={`grid${list.loading && list.data ? ' is-refreshing' : ''}`}>
            {!list.data ? (
              <CardSkeletons count={12} />
            ) : (
              items.map((r, i) => (
                <RecipeCard
                  key={r.id}
                  recipe={r}
                  priority={i < 6}
                  onFavourite={toggleFav}
                  onAdd={addMode ? addToPlan : undefined}
                  added={inPlan.has(r.id)}
                />
              ))
            )}
          </div>
          {list.data && list.data.total > items.length && (
            <div className="more">
              <button type="button" className="btn" onClick={() => setLimit((l) => l + PAGE)} disabled={list.loading}>
                {list.loading ? 'Loading…' : `Show more (${list.data.total - items.length} left)`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
