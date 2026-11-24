import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { Day, Plan, RecipeDetail } from '../api/types'
import { Icon } from '../components/Icon'
import { IngredientGroups } from '../components/Ingredients'
import { MacroBar } from '../components/MacroBar'
import { MacroFigures } from '../components/Macros'
import { Photo } from '../components/Photo'
import { EmptyState, ErrorState, Spinner } from '../components/States'
import { Stepper } from '../components/Stepper'
import { useToast } from '../lib/toast'
import { useFetch } from '../lib/useFetch'
import { DAYS } from '../lib/week'

const VIDEO_LABELS: Record<string, string> = { youtube: 'YouTube', tiktok: 'TikTok', instagram: 'Instagram' }

export function RecipePage() {
  const { slug = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const servingsParam = params.get('servings')
  const servings = servingsParam ? Number(servingsParam) : undefined

  const recipe = useFetch<RecipeDetail>(() => api.recipe(slug, servings), `${slug}:${servings}`)
  const plan = useFetch<Plan>(() => api.currentPlan(), 'plan')
  const [day, setDay] = useState<Day | ''>('')
  const [busy, setBusy] = useState(false)
  const [fav, setFav] = useState<boolean>()
  useEffect(() => setFav(recipe.data?.favourite), [recipe.data?.favourite])

  const r = recipe.data
  if (recipe.error) {
    if (recipe.error instanceof ApiError && recipe.error.status === 404) {
      return <EmptyState title="Recipe not found" action={<Link className="btn btn-primary" to="/">Back to recipes</Link>}><p>It may have been deleted or renamed.</p></EmptyState>
    }
    return <ErrorState error={recipe.error} onRetry={recipe.reload} />
  }
  if (!r) return <RecipeSkeleton />

  const current = r.scaled_servings ?? r.servings ?? 1
  const bookServings = r.servings ?? 1
  const entry = plan.data?.entries.find((e) => e.recipe.id === r.id)

  function setServings(n: number) {
    const next = new URLSearchParams(params)
    if (n === bookServings) next.delete('servings')
    else next.set('servings', String(n))
    setParams(next, { replace: true })
  }

  async function toggleFav() {
    if (!r) return
    const on = !fav
    setFav(on)
    try {
      await api.setFavourite(r.id, on)
    } catch (e) {
      setFav(!on)
      toast({ text: `Couldn't update favourite: ${(e as Error).message}`, tone: 'error' })
    }
  }

  async function addToPlan() {
    if (!r || !plan.data) return
    setBusy(true)
    try {
      const next = entry
        ? await api.updateEntry(plan.data.id, entry.id, { servings: current, ...(day ? { day } : {}) })
        : await api.addEntry(plan.data.id, { recipe_id: r.id, servings: current, day: day || null })
      plan.setData(next)
      toast({ text: entry ? `Plan updated: ${current} servings` : `Added to this week: ${current} servings`, link: { to: '/plan', label: 'View plan' } })
    } catch (e) {
      toast({ text: `Couldn't add to plan: ${(e as Error).message}`, tone: 'error' })
    } finally {
      setBusy(false)
    }
  }

  const videos = Object.entries(r.videos ?? {}).filter(([, url]) => url)
  const cookHref = `/r/${r.slug}/cook${servings ? `?servings=${servings}` : ''}`

  return (
    <article className="recipe">
      <div className="recipe-hero">
        <Photo src={r.image_url} alt={r.title} className="recipe-photo" eager />
        <button type="button" className="recipe-back" onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/'))} aria-label="Back">
          <Icon name="back" size={22} />
        </button>
      </div>

      <div className="recipe-head">
        <p className="recipe-source">
          {r.source ? (
            <><Icon name="book" size={16} /> {r.source.name}{r.source_page ? <>, page {r.source_page}</> : null}</>
          ) : (
            <>Your recipe</>
          )}
          {r.user_edited && r.source && <span className="badge">Edited</span>}
        </p>
        <h1 className="recipe-title">{r.title}</h1>
        {r.blurb && <p className="recipe-blurb">{r.blurb}</p>}

        <section className="recipe-macros" aria-labelledby="macros-h">
          <h2 id="macros-h" className="sr-only">Macros per serving</h2>
          <MacroFigures m={r} size="lg" caption="Per serving" />
          <MacroBar protein={r.protein} carbs={r.carbs} fat={r.fat} size="md" />
          <p className="recipe-macros-note">Per serving{r.servings_text ? ` · ${r.servings_text}` : ''}</p>
        </section>

        <div className="recipe-actions">
          <Link className="btn btn-primary btn-lg" to={cookHref}>
            <Icon name="cook" size={20} /> Start cooking
          </Link>
          <button type="button" className={`btn btn-icon btn-lg fav-toggle${fav ? ' is-on' : ''}`} aria-pressed={!!fav} onClick={toggleFav} aria-label={fav ? 'Remove from favourites' : 'Add to favourites'}>
            <Icon name="heart" size={22} filled={!!fav} />
          </button>
          <Link className="btn btn-icon btn-lg" to={`/r/${r.slug}/edit`} aria-label="Edit recipe">
            <Icon name="edit" size={20} />
          </Link>
        </div>

        <section className="planbox" aria-labelledby="planbox-h">
          <h2 id="planbox-h">This week</h2>
          <div className="planbox-row">
            <label className="select select-compact">
              <span className="sr-only">Day</span>
              <select value={day} onChange={(e) => setDay(e.target.value as Day | '')}>
                <option value="">Any day</option>
                {DAYS.map((d) => <option key={d.id} value={d.id}>{d.long}</option>)}
              </select>
            </label>
            <button type="button" className="btn btn-secondary" onClick={addToPlan} disabled={busy || !plan.data}>
              {busy ? <Spinner label="Saving" /> : <Icon name={entry && entry.servings === current ? 'check' : 'plan'} size={18} />}
              {entry ? (entry.servings === current ? `In plan · ${entry.servings} servings` : `Update plan to ${current}`) : `Add ${current} ${current === 1 ? 'serving' : 'servings'}`}
            </button>
          </div>
        </section>
      </div>

      <div className="recipe-body">
        <section className="recipe-ingredients" aria-labelledby="ing-h">
          <div className="section-head">
            <h2 id="ing-h">Ingredients</h2>
            <Stepper label="Servings" value={current} onChange={setServings} suffix={current === 1 ? 'serving' : 'servings'} />
          </div>
          {current !== bookServings && (
            <p className="scale-note">
              Scaled ×{Math.round(r.scale * 100) / 100} from the book's {bookServings}.{' '}
              <button type="button" className="linkbtn" onClick={() => setServings(bookServings)}>Reset</button>
            </p>
          )}
          <div className={recipe.loading ? 'is-refreshing' : ''}>
            <IngredientGroups groups={r.groups} />
          </div>
        </section>

        <section className="recipe-steps" aria-labelledby="steps-h">
          <h2 id="steps-h">Method</h2>
          <ol className="steps">
            {r.steps.map((s, i) => (
              <li key={i}><span className="step-n" aria-hidden="true">{i + 1}</span><p>{s}</p></li>
            ))}
          </ol>
          {r.notes.length > 0 && (
            <div className="tips">
              <h3>Tips</h3>
              <ul>{r.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
            </div>
          )}
          {videos.length > 0 && (
            <div className="videos">
              <h3>Watch it made</h3>
              <ul>
                {videos.map(([site, url]) => (
                  <li key={site}>
                    <a href={url} target="_blank" rel="noreferrer" className="btn">
                      <Icon name="play" size={18} /> {VIDEO_LABELS[site] ?? site}
                      <Icon name="external" size={14} className="ext" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </article>
  )
}

function RecipeSkeleton() {
  return (
    <div className="recipe" aria-busy="true">
      <div className="recipe-hero"><div className="photo recipe-photo skel" /></div>
      <div className="recipe-head">
        <div className="skel skel-line short" />
        <div className="skel skel-title" />
        <div className="skel skel-line" />
        <div className="skel skel-line" />
      </div>
    </div>
  )
}
