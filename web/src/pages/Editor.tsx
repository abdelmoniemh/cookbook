import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { RecipeDetail, RecipeInput } from '../api/types'
import { PageHeader } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { ErrorState, Spinner } from '../components/States'
import { useToast } from '../lib/toast'
import { useFetch } from '../lib/useFetch'

type Group = { name: string; note: string; text: string }
type Form = {
  title: string; blurb: string; servings: string
  kcal: string; protein: string; carbs: string; fat: string
  tags: string[]; groups: Group[]; steps: string[]; notes: string
}

const EMPTY: Form = {
  title: '', blurb: '', servings: '4', kcal: '', protein: '', carbs: '', fat: '',
  tags: [], groups: [{ name: '', note: '', text: '' }], steps: [''], notes: '',
}

function fromRecipe(r: RecipeDetail): Form {
  const s = (n: number | null) => (n == null ? '' : String(n))
  return {
    title: r.title, blurb: r.blurb ?? '', servings: s(r.servings),
    kcal: s(r.kcal), protein: s(r.protein), carbs: s(r.carbs), fat: s(r.fat),
    tags: r.tags,
    groups: r.groups.length ? r.groups.map((g) => ({ name: g.name ?? '', note: g.note ?? '', text: g.items.map((i) => i.raw).join('\n') })) : EMPTY.groups,
    steps: r.steps.length ? r.steps : [''],
    notes: r.notes.join('\n'),
  }
}

function toInput(f: Form): RecipeInput {
  const n = (v: string) => (v.trim() === '' ? null : Number(v))
  return {
    title: f.title.trim(),
    blurb: f.blurb.trim() || null,
    servings: n(f.servings),
    kcal: n(f.kcal), protein: n(f.protein), carbs: n(f.carbs), fat: n(f.fat),
    tags: f.tags,
    groups: f.groups
      .map((g) => ({ name: g.name.trim() || null, note: g.note.trim() || null, lines: g.text.split('\n').map((l) => l.trim()).filter(Boolean) }))
      .filter((g) => g.lines.length || g.name),
    steps: f.steps.map((s) => s.trim()).filter(Boolean),
    notes: f.notes.split('\n').map((l) => l.trim()).filter(Boolean),
  }
}

export function EditorPage() {
  const { slug } = useParams()
  const editing = Boolean(slug)
  const navigate = useNavigate()
  const toast = useToast()
  const existing = useFetch<RecipeDetail | undefined>(() => (slug ? api.recipe(slug) : Promise.resolve(undefined)), slug ?? 'new')
  const tagList = useFetch(() => api.tags(), 'tags')
  const [form, setForm] = useState<Form>(EMPTY)
  const [tagText, setTagText] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string>()
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => { if (existing.data) setForm(fromRecipe(existing.data)) }, [existing.data])

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => ({ ...f, [k]: v }))
  const setGroup = (i: number, patch: Partial<Group>) => set('groups', form.groups.map((g, j) => (j === i ? { ...g, ...patch } : g)))
  const addTag = (t: string) => {
    const tag = t.trim().toLowerCase()
    if (tag && !form.tags.includes(tag)) set('tags', [...form.tags, tag])
    setTagText('')
  }

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const input = toInput(form)
    if (!input.title) return setError('Give the recipe a title.')
    if (!input.groups.some((g) => g.lines.length)) return setError('Add at least one ingredient line.')
    setError(undefined)
    setSaving(true)
    try {
      const saved = editing && existing.data ? await api.updateRecipe(existing.data.id, input) : await api.createRecipe(input)
      toast({ text: editing ? 'Recipe saved' : 'Recipe added' })
      navigate(`/r/${saved.slug}`, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (!existing.data) return
    if (!confirmDelete) return setConfirmDelete(true)
    try {
      await api.deleteRecipe(existing.data.id)
      toast({ text: `Deleted ${existing.data.title}` })
      navigate('/', { replace: true })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (existing.error) return <ErrorState error={existing.error} onRetry={existing.reload} />
  if (editing && !existing.data) return <div className="state"><Spinner /></div>

  const suggestions = (tagList.data ?? []).map((t) => t.tag).filter((t) => !form.tags.includes(t) && (!tagText || t.includes(tagText.toLowerCase()))).slice(0, 10)

  return (
    <div className="editor narrow">
      <PageHeader
        title={editing ? 'Edit recipe' : 'New recipe'}
        sub={editing ? (existing.data?.source ? <>From {existing.data.source.name}. Saving keeps your version when the book is re-imported.</> : null) : <>Or <Link to="/import">import a cookbook PDF</Link>.</>}
      />

      <form onSubmit={save} className="form" noValidate>
        <fieldset className="panel">
          <legend>Basics</legend>
          <div className="field">
            <label htmlFor="f-title">Title</label>
            <input id="f-title" value={form.title} onChange={(e) => set('title', e.target.value)} required autoComplete="off" />
          </div>
          <div className="field">
            <label htmlFor="f-blurb">Description <span className="opt">optional</span></label>
            <textarea id="f-blurb" rows={2} value={form.blurb} onChange={(e) => set('blurb', e.target.value)} />
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="f-servings">Servings</label>
              <input id="f-servings" type="number" inputMode="decimal" min={1} value={form.servings} onChange={(e) => set('servings', e.target.value)} />
            </div>
            {(['kcal', 'protein', 'carbs', 'fat'] as const).map((k) => (
              <div className={`field field-${k}`} key={k}>
                <label htmlFor={`f-${k}`}><span className="key" aria-hidden="true" />{k === 'kcal' ? 'kcal' : `${k[0].toUpperCase()}${k.slice(1)} (g)`}</label>
                <input id={`f-${k}`} type="number" inputMode="decimal" min={0} value={form[k]} onChange={(e) => set(k, e.target.value)} />
              </div>
            ))}
          </div>
          <p className="field-help">Macros are per serving.</p>

          <div className="field">
            <label htmlFor="f-tags">Tags</label>
            <div className="tag-input">
              {form.tags.map((t) => (
                <span className="chip is-on" key={t}>
                  {t}
                  <button type="button" aria-label={`Remove tag ${t}`} onClick={() => set('tags', form.tags.filter((x) => x !== t))}><Icon name="close" size={14} /></button>
                </span>
              ))}
              <input
                id="f-tags"
                value={tagText}
                placeholder={form.tags.length ? '' : 'chicken, meal prep…'}
                onChange={(e) => setTagText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addTag(tagText) }
                  if (e.key === 'Backspace' && !tagText && form.tags.length) set('tags', form.tags.slice(0, -1))
                }}
                onBlur={() => tagText && addTag(tagText)}
              />
            </div>
            {suggestions.length > 0 && (
              <div className="chips chips-wrap">
                {suggestions.map((t) => <button type="button" className="chip" key={t} onClick={() => addTag(t)}><Icon name="plus" size={14} />{t}</button>)}
              </div>
            )}
          </div>
        </fieldset>

        <fieldset className="panel">
          <legend>Ingredients</legend>
          <p className="field-help">One ingredient per line, amount first: <code>800g chicken breast, cubed</code>. Lines like “Use any rice you have” are kept as notes and left off the shopping list.</p>
          {form.groups.map((g, i) => (
            <div className="group-edit" key={i}>
              <div className="field-row">
                <div className="field grow">
                  <label htmlFor={`g-name-${i}`}>Group name <span className="opt">optional</span></label>
                  <input id={`g-name-${i}`} value={g.name} placeholder={i === 0 ? 'e.g. Chicken' : 'e.g. Sauce'} onChange={(e) => setGroup(i, { name: e.target.value })} />
                </div>
                {form.groups.length > 1 && (
                  <button type="button" className="btn btn-icon btn-ghost group-remove" onClick={() => set('groups', form.groups.filter((_, j) => j !== i))} aria-label={`Remove group ${g.name || i + 1}`}>
                    <Icon name="trash" size={20} />
                  </button>
                )}
              </div>
              <div className="field">
                <label htmlFor={`g-lines-${i}`}>Lines</label>
                <textarea id={`g-lines-${i}`} rows={Math.max(4, g.text.split('\n').length + 1)} value={g.text} onChange={(e) => setGroup(i, { text: e.target.value })} className="mono-ish" />
              </div>
            </div>
          ))}
          <button type="button" className="btn" onClick={() => set('groups', [...form.groups, { name: '', note: '', text: '' }])}><Icon name="plus" size={18} /> Add a group</button>
        </fieldset>

        <fieldset className="panel">
          <legend>Method</legend>
          <ol className="steps-edit">
            {form.steps.map((s, i) => (
              <li key={i}>
                <span className="step-n" aria-hidden="true">{i + 1}</span>
                <label className="sr-only" htmlFor={`s-${i}`}>Step {i + 1}</label>
                <textarea id={`s-${i}`} rows={2} value={s} onChange={(e) => set('steps', form.steps.map((x, j) => (j === i ? e.target.value : x)))} />
                {form.steps.length > 1 && (
                  <button type="button" className="btn btn-icon btn-ghost" onClick={() => set('steps', form.steps.filter((_, j) => j !== i))} aria-label={`Remove step ${i + 1}`}>
                    <Icon name="close" size={18} />
                  </button>
                )}
              </li>
            ))}
          </ol>
          <button type="button" className="btn" onClick={() => set('steps', [...form.steps, ''])}><Icon name="plus" size={18} /> Add a step</button>
        </fieldset>

        <fieldset className="panel">
          <legend>Tips</legend>
          <div className="field">
            <label htmlFor="f-notes">One tip per line <span className="opt">optional</span></label>
            <textarea id="f-notes" rows={3} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
          </div>
        </fieldset>

        {error && <p className="form-error" role="alert"><Icon name="alert" size={18} /> {error}</p>}

        <div className="form-actions sticky-actions">
          {editing && (
            <button type="button" className={`btn btn-danger${confirmDelete ? ' is-armed' : ''}`} onClick={remove} onBlur={() => setConfirmDelete(false)}>
              <Icon name="trash" size={18} /> {confirmDelete ? 'Tap again to delete' : 'Delete'}
            </button>
          )}
          <span className="spacer" />
          <Link className="btn btn-ghost" to={editing ? `/r/${slug}` : '/'}>Cancel</Link>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
            {saving ? <Spinner label="Saving" /> : <Icon name="check" size={20} />} {editing ? 'Save changes' : 'Add recipe'}
          </button>
        </div>
      </form>
    </div>
  )
}
