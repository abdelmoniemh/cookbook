// Small fetch client for the cookbook API (docs/API.md).
import type {
  Day, ImportResult, Plan, RecipeDetail, RecipeInput, RecipeList, RecipeQuery, RecipeSummary,
  ShoppingList, SourceCount, TagCount,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData)) headers.set('content-type', 'application/json')
  let res: Response
  try {
    res = await fetch(path, { ...init, headers })
  } catch {
    throw new ApiError(0, "Can't reach the cookbook server. Is it running?")
  }
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') message = body.detail
      else if (Array.isArray(body?.detail)) message = body.detail.map((d: { msg?: string }) => d.msg).join('; ')
    } catch {
      // Not JSON: usually a proxy or the server itself being down.
      if (res.status >= 500) message = `The cookbook server isn't responding (${res.status}). Is it running?`
    }
    throw new ApiError(res.status, message)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) })

function qs(params: Record<string, string | number | boolean | string[] | undefined | null>): string {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, x))
    else sp.set(k, String(v))
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const api = {
  health: () => request<{ ok: true; recipes: number }>('/api/health'),

  recipes: (query: RecipeQuery = {}) => request<RecipeList>(`/api/recipes${qs(query)}`),
  recipe: (idOrSlug: string | number, servings?: number) =>
    request<RecipeDetail>(`/api/recipes/${encodeURIComponent(idOrSlug)}${qs({ servings })}`),
  createRecipe: (input: RecipeInput) => request<RecipeDetail>('/api/recipes', json('POST', input)),
  updateRecipe: (id: number, input: RecipeInput) => request<RecipeDetail>(`/api/recipes/${id}`, json('PUT', input)),
  deleteRecipe: (id: number) => request<void>(`/api/recipes/${id}`, { method: 'DELETE' }),
  setFavourite: (id: number, favourite: boolean) =>
    request<RecipeSummary>(`/api/recipes/${id}/favourite`, json('PUT', { favourite })),

  tags: () => request<TagCount[]>('/api/tags'),
  sources: () => request<SourceCount[]>('/api/sources'),

  /** Uploads a PDF. Uses XHR so the page can show upload progress; `onProgress` gets 0..1. */
  importPdf: (file: File, onProgress?: (fraction: number) => void, signal?: AbortSignal) =>
    new Promise<ImportResult>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/import')
      xhr.responseType = 'json'
      xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress?.(e.loaded / e.total) }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) return resolve(xhr.response as ImportResult)
        const detail = (xhr.response as { detail?: unknown } | null)?.detail
        reject(new ApiError(xhr.status, typeof detail === 'string' ? detail : `Import failed (${xhr.status})`))
      }
      xhr.onerror = () => reject(new ApiError(0, "Can't reach the cookbook server. Is it running?"))
      xhr.onabort = () => reject(new ApiError(0, 'Import cancelled'))
      signal?.addEventListener('abort', () => xhr.abort())
      const body = new FormData()
      body.append('file', file)
      xhr.send(body)
    }),

  currentPlan: (week?: string) => request<Plan>(`/api/plans/current${qs({ week })}`),
  addEntry: (planId: number, body: { recipe_id: number; servings?: number; day?: Day | null }) =>
    request<Plan>(`/api/plans/${planId}/entries`, json('POST', body)),
  updateEntry: (planId: number, entryId: number, body: { servings?: number; day?: Day | null; position?: number }) =>
    request<Plan>(`/api/plans/${planId}/entries/${entryId}`, json('PATCH', body)),
  removeEntry: (planId: number, entryId: number) =>
    request<Plan>(`/api/plans/${planId}/entries/${entryId}`, { method: 'DELETE' }),

  shopping: (planId: number) => request<ShoppingList>(`/api/plans/${planId}/shopping`),
  setChecked: (planId: number, key: string, checked: boolean) =>
    request<ShoppingList>(`/api/plans/${planId}/shopping/checked`, json('PUT', { key, checked })),
  addExtra: (planId: number, text: string) =>
    request<ShoppingList>(`/api/plans/${planId}/shopping/extras`, json('POST', { text })),
  removeExtra: (planId: number, extraId: string | number) =>
    request<ShoppingList>(`/api/plans/${planId}/shopping/extras/${extraId}`, { method: 'DELETE' }),
}
