// Dev-only mock of the cookbook API (docs/API.md), backed by synthetic data in memory.
// Usage: npm run mock   (listens on 127.0.0.1:8787), then npm run dev:mock
// MOCK_EMPTY=1 starts with no recipes, to see the first-run state.
import http from 'node:http'
import { SOURCES, buildRecipes, placeholderSvg } from './data.mjs'

const PORT = Number(process.env.MOCK_PORT || 8787)
let recipes = process.env.MOCK_EMPTY ? [] : buildRecipes()
let nextRecipeId = recipes.length + 1
let nextIngId = 10000
const plans = new Map() // week_start -> plan
let nextPlanId = 1
let nextEntryId = 1
let nextExtraId = 1

const AISLES = ['Produce', 'Meat & Fish', 'Dairy & Eggs', 'Pasta, Rice & Grains', 'Sauces & Pantry', 'Spices & Seasonings', 'Other']

// ---------- helpers ----------
const round = (n) => Math.round(n * 100) / 100
function fmtQty(q) {
  if (q == null) return ''
  if (q >= 100) return String(Math.round(q))
  if (Number.isInteger(q)) return String(q)
  return String(Math.round(q * 10) / 10)
}
function fmtAmount(qty, unit) {
  if (qty == null) return ''
  if (unit === 'g' && qty >= 1000) return `${fmtQty(qty / 1000)} kg`
  if (unit === 'ml' && qty >= 1000) return `${fmtQty(qty / 1000)} l`
  if (!unit) return fmtQty(qty)
  const spaced = ['g', 'ml', 'kg', 'l'].includes(unit) ? unit : ` ${unit}`
  return `${fmtQty(qty)}${spaced.startsWith(' ') ? spaced : ' ' + spaced}`
}
function ingredientOut(it, scale) {
  if (it.kind === 'note') {
    return { id: it.id, kind: 'note', raw: it.raw, qty: null, qty_max: null, unit: null, alt_measure: null, item: it.raw, prep: null, note: null, canonical: '', aisle: 'Skip', each_of: [], display: it.raw }
  }
  const qty = it.qty == null ? null : round(it.qty * scale)
  const amount = fmtAmount(qty, it.unit)
  const raw = `${fmtAmount(it.qty, it.unit)} ${it.item}${it.prep ? `, ${it.prep}` : ''}`.trim()
  return {
    id: it.id, kind: 'item', raw, qty, qty_max: null, unit: it.unit ?? null, alt_measure: null,
    item: it.item, prep: it.prep ?? null, note: it.note ?? null,
    canonical: it.canonical ?? it.item.toLowerCase(), aisle: it.aisle ?? 'Other', each_of: [],
    display: `${amount ? amount + ' ' : ''}${it.item}${it.prep ? `, ${it.prep}` : ''}`,
  }
}
function summary(r) {
  const src = SOURCES.find((s) => s.id === r.source_id)
  return {
    id: r.id, slug: r.slug, title: r.title, blurb: r.blurb, image_url: r.image_url,
    kcal: r.kcal, protein: r.protein, carbs: r.carbs, fat: r.fat, servings: r.servings,
    tags: r.tags, source: src ? { id: src.id, name: src.name } : null, favourite: r.favourite,
  }
}
function detail(r, servings) {
  const base = r.servings || 1
  const target = servings ?? r.servings
  const scale = target ? target / base : 1
  return {
    ...summary(r),
    servings_text: r.servings_text, videos: r.videos, source_page: r.source_page,
    scale: round(scale), scaled_servings: target ?? null,
    groups: r.groups.map((g) => ({ name: g.name, note: g.note, items: g.items.map((it) => ingredientOut(it, scale)) })),
    steps: r.steps, notes: r.notes, user_edited: r.user_edited,
  }
}
function findRecipe(key) {
  return recipes.find((r) => String(r.id) === key || r.slug === key)
}
function mondayOf(d) {
  const dt = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
  const day = (dt.getUTCDay() + 6) % 7
  dt.setUTCDate(dt.getUTCDate() - day)
  return dt.toISOString().slice(0, 10)
}
function getPlan(weekStart) {
  if (!plans.has(weekStart)) plans.set(weekStart, { id: nextPlanId++, week_start: weekStart, entries: [], checked: new Set(), extras: [] })
  return plans.get(weekStart)
}
function planById(id) {
  return [...plans.values()].find((p) => p.id === Number(id))
}
function planOut(p) {
  const entries = p.entries
    .filter((e) => findRecipe(String(e.recipe_id)))
    .map((e) => ({ id: e.id, recipe: summary(findRecipe(String(e.recipe_id))), servings: e.servings, day: e.day, position: e.position }))
  const totals = { servings: 0, kcal: 0, protein: 0, carbs: 0, fat: 0 }
  for (const e of entries) {
    totals.servings += e.servings
    for (const k of ['kcal', 'protein', 'carbs', 'fat']) totals[k] += (e.recipe[k] ?? 0) * e.servings
  }
  for (const k of Object.keys(totals)) totals[k] = round(totals[k])
  return { id: p.id, week_start: p.week_start, entries: entries.sort((a, b) => a.position - b.position), totals }
}
const UNIT_FAMILY = { g: ['g', 1], kg: ['g', 1000], oz: ['g', 28.35], lb: ['g', 453.6], ml: ['ml', 1], l: ['ml', 1000], tsp: ['ml', 5], tbsp: ['ml', 15], cup: ['ml', 240] }
function shoppingOut(p) {
  const map = new Map()
  for (const e of p.entries) {
    const r = findRecipe(String(e.recipe_id))
    if (!r) continue
    const scale = e.servings / (r.servings || 1)
    for (const g of r.groups) for (const it of g.items) {
      if (it.kind === 'note' || it.aisle === 'Skip') continue
      const canonical = it.canonical ?? it.item.toLowerCase()
      const fam = it.unit ? (UNIT_FAMILY[it.unit] ?? [it.unit, 1]) : [it.qty == null ? 'none' : 'count', 1]
      const key = `${canonical}|${fam[0]}`
      const cur = map.get(key) ?? { key, name: canonical[0].toUpperCase() + canonical.slice(1), qty: null, unit: fam[0], aisle: it.aisle, recipes: new Set() }
      if (it.qty != null) cur.qty = (cur.qty ?? 0) + it.qty * scale * fam[1]
      cur.recipes.add(r.title)
      map.set(key, cur)
    }
  }
  const byAisle = new Map([...AISLES, 'Extras'].map((a) => [a, []]))
  for (const c of map.values()) {
    let display = 'as needed'
    let unit = ['none', 'count'].includes(c.unit) ? null : c.unit
    if (c.qty != null) {
      if (unit === 'ml' && c.qty < 60) display = c.qty % 15 === 0 ? `${fmtQty(c.qty / 15)} tbsp` : `${fmtQty(c.qty / 5)} tsp`
      else display = fmtAmount(round(c.qty), unit)
    }
    byAisle.get(c.aisle)?.push({ key: c.key, name: c.name, qty: c.qty == null ? null : round(c.qty), unit, display, recipes: [...c.recipes], checked: p.checked.has(c.key), extra: false })
  }
  for (const x of p.extras) {
    byAisle.get('Extras').push({ key: `extra:${x.id}`, name: x.text, qty: null, unit: null, display: '', recipes: [], checked: p.checked.has(`extra:${x.id}`), extra: true })
  }
  return {
    plan_id: p.id,
    aisles: [...byAisle.entries()].filter(([, items]) => items.length).map(([aisle, items]) => ({ aisle, items: aisle === 'Extras' ? items : items.sort((a, b) => a.name.localeCompare(b.name)) })),
  }
}
function parseLine(line) {
  const m = line.trim().match(/^(\d+(?:\.\d+)?)\s*(g|kg|ml|l|tsp|tbsp|cup|scoop|clove|slice|can)?\s+(.*)$/i)
  if (!m) return { id: nextIngId++, kind: line.trim().endsWith(':') || /^(use|optional|note)/i.test(line) ? 'note' : 'item', raw: line, qty: null, unit: null, item: line.trim(), aisle: 'Other' }
  const [, q, unit, rest] = m
  const [item, prep] = rest.split(/,\s*/, 2)
  return { id: nextIngId++, kind: 'item', raw: line, qty: Number(q), unit: unit ? unit.toLowerCase() : null, item, prep: prep ?? null, canonical: item.toLowerCase(), aisle: 'Other' }
}
function applyInput(r, body) {
  r.title = body.title
  r.slug = r.slug ?? body.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  r.blurb = body.blurb ?? null
  r.servings = body.servings ?? null
  r.servings_text = body.servings ? `Serves ${body.servings}` : null
  for (const k of ['kcal', 'protein', 'carbs', 'fat']) r[k] = body[k] ?? null
  r.tags = body.tags ?? []
  r.groups = (body.groups ?? []).map((g) => ({ name: g.name, note: g.note ?? null, items: g.lines.filter((l) => l.trim()).map(parseLine) }))
  r.steps = body.steps ?? []
  r.notes = body.notes ?? []
}

// ---------- http ----------
function send(res, status, body, type = 'application/json') {
  res.writeHead(status, { 'content-type': type, 'cache-control': 'no-store' })
  res.end(type === 'application/json' ? JSON.stringify(body) : body)
}
async function readBody(req) {
  const chunks = []
  for await (const c of req) chunks.push(c)
  const buf = Buffer.concat(chunks)
  const ct = req.headers['content-type'] || ''
  if (ct.includes('application/json')) return JSON.parse(buf.toString() || '{}')
  return buf
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const LATENCY = Number(process.env.MOCK_LATENCY || 120)

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`)
  const path = url.pathname
  const q = url.searchParams
  const parts = path.split('/').filter(Boolean)
  try {
    if (path.startsWith('/images/')) {
      const slug = decodeURIComponent(path.slice(8)).replace(/\.svg$/, '')
      return send(res, 200, placeholderSvg(recipes.find((r) => r.slug === slug)), 'image/svg+xml')
    }
    if (!path.startsWith('/api/')) return send(res, 404, { detail: 'Not found' })
    await sleep(LATENCY)
    const m = req.method

    if (path === '/api/health') return send(res, 200, { ok: true, recipes: recipes.length })
    if (path === '/api/tags') {
      const counts = new Map()
      for (const r of recipes) for (const t of r.tags) counts.set(t, (counts.get(t) ?? 0) + 1)
      return send(res, 200, [...counts].map(([tag, count]) => ({ tag, count })).sort((a, b) => b.count - a.count))
    }
    if (path === '/api/sources') {
      return send(res, 200, SOURCES.map((s) => ({ ...s, recipe_count: recipes.filter((r) => r.source_id === s.id).length })).filter((s) => s.recipe_count))
    }
    if (path === '/api/import' && m === 'POST') {
      await readBody(req)
      await sleep(2500)
      return send(res, 200, {
        source: 'Demo Upload Book', added: 3, updated: 1, kept: 0,
        warnings: [{ title: 'Demo Chilli Con Carne', page: 14, warnings: ['Ingredient "1 tsp" has no name', 'No servings found; assumed 1'] }],
      })
    }
    if (parts[1] === 'recipes') {
      if (parts.length === 2 && m === 'GET') {
        let list = [...recipes]
        const text = (q.get('q') || '').toLowerCase().trim()
        if (text) list = list.filter((r) => [r.title, r.blurb, r.tags.join(' '), ...r.groups.flatMap((g) => g.items.map((i) => i.item || ''))].join(' ').toLowerCase().includes(text))
        for (const t of q.getAll('tag')) list = list.filter((r) => r.tags.includes(t))
        if (q.get('source')) list = list.filter((r) => r.source_id === Number(q.get('source')))
        if (q.get('favourite') === 'true') list = list.filter((r) => r.favourite)
        if (q.get('max_kcal')) list = list.filter((r) => (r.kcal ?? 0) <= Number(q.get('max_kcal')))
        if (q.get('min_protein')) list = list.filter((r) => (r.protein ?? 0) >= Number(q.get('min_protein')))
        const sort = q.get('sort') || 'title'
        if (sort === 'title') list.sort((a, b) => a.title.localeCompare(b.title))
        if (sort === 'protein') list.sort((a, b) => (b.protein ?? 0) - (a.protein ?? 0))
        if (sort === 'kcal') list.sort((a, b) => (a.kcal ?? 0) - (b.kcal ?? 0))
        if (sort === 'recent') list.sort((a, b) => b.created - a.created)
        const offset = Number(q.get('offset') || 0)
        const limit = Number(q.get('limit') || 50)
        return send(res, 200, { items: list.slice(offset, offset + limit).map(summary), total: list.length })
      }
      if (parts.length === 2 && m === 'POST') {
        const body = await readBody(req)
        if (!body.title?.trim()) return send(res, 422, { detail: 'Title is required' })
        const r = { id: nextRecipeId++, source_id: null, source_page: null, favourite: false, videos: {}, user_edited: false, image_url: null, created: Date.now() }
        applyInput(r, body)
        recipes.push(r)
        return send(res, 201, detail(r))
      }
      const r = findRecipe(decodeURIComponent(parts[2]))
      if (!r) return send(res, 404, { detail: 'Recipe not found' })
      if (parts[3] === 'favourite' && m === 'PUT') {
        const body = await readBody(req)
        r.favourite = !!body.favourite
        return send(res, 200, summary(r))
      }
      if (m === 'GET') return send(res, 200, detail(r, q.get('servings') ? Number(q.get('servings')) : undefined))
      if (m === 'PUT') { applyInput(r, await readBody(req)); r.user_edited = true; return send(res, 200, detail(r)) }
      if (m === 'DELETE') { recipes = recipes.filter((x) => x !== r); res.writeHead(204); return res.end() }
    }
    if (parts[1] === 'plans') {
      if (parts[2] === 'current') {
        const wk = q.get('week') ? new Date(q.get('week') + 'T00:00:00Z') : new Date()
        return send(res, 200, planOut(getPlan(mondayOf(wk))))
      }
      const p = planById(parts[2])
      if (!p) return send(res, 404, { detail: 'Plan not found' })
      if (parts[3] === 'entries') {
        if (m === 'POST') {
          const body = await readBody(req)
          const r = findRecipe(String(body.recipe_id))
          if (!r) return send(res, 404, { detail: 'Recipe not found' })
          p.entries.push({ id: nextEntryId++, recipe_id: r.id, servings: body.servings ?? r.servings ?? 1, day: body.day ?? null, position: p.entries.length })
          return send(res, 200, planOut(p))
        }
        const e = p.entries.find((x) => x.id === Number(parts[4]))
        if (!e) return send(res, 404, { detail: 'Entry not found' })
        if (m === 'PATCH') {
          const body = await readBody(req)
          if (body.servings !== undefined) e.servings = body.servings
          if (body.day !== undefined) e.day = body.day
          if (body.position !== undefined) e.position = body.position
          return send(res, 200, planOut(p))
        }
        if (m === 'DELETE') { p.entries = p.entries.filter((x) => x !== e); return send(res, 200, planOut(p)) }
      }
      if (parts[3] === 'shopping') {
        if (parts.length === 4 && m === 'GET') return send(res, 200, shoppingOut(p))
        if (parts[4] === 'checked' && m === 'PUT') {
          const body = await readBody(req)
          if (body.checked) p.checked.add(body.key); else p.checked.delete(body.key)
          return send(res, 200, shoppingOut(p))
        }
        if (parts[4] === 'extras' && m === 'POST') {
          const body = await readBody(req)
          if (!body.text?.trim()) return send(res, 422, { detail: 'Text is required' })
          p.extras.push({ id: nextExtraId++, text: body.text.trim() })
          return send(res, 200, shoppingOut(p))
        }
        if (parts[4] === 'extras' && m === 'DELETE') {
          p.extras = p.extras.filter((x) => x.id !== Number(parts[5]))
          return send(res, 200, shoppingOut(p))
        }
      }
    }
    return send(res, 404, { detail: 'Not found' })
  } catch (err) {
    console.error(err)
    return send(res, 500, { detail: String(err) })
  }
})

// Seed this week's plan with two meal preps and a breakfast so Plan and Shopping have something to show.
if (!process.env.MOCK_EMPTY && !process.env.MOCK_EMPTY_PLAN) {
  const p = getPlan(mondayOf(new Date()))
  for (const [rid, servings, day] of [[1, 4, 'sun'], [2, 4, 'sun'], [3, 2, null]]) {
    p.entries.push({ id: nextEntryId++, recipe_id: rid, servings, day, position: p.entries.length })
  }
}

server.listen(PORT, '127.0.0.1', () => console.log(`mock API on http://127.0.0.1:${PORT}`))
