import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { ImportResult } from '../api/types'
import { PageHeader } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { Spinner } from '../components/States'

type Phase = { kind: 'idle' } | { kind: 'uploading'; fraction: number } | { kind: 'processing' } | { kind: 'done'; result: ImportResult } | { kind: 'error'; message: string }

export function ImportPage() {
  const [file, setFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<Phase>({ kind: 'idle' })
  const abort = useRef<AbortController | null>(null)
  const busy = phase.kind === 'uploading' || phase.kind === 'processing'

  async function start(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    abort.current = new AbortController()
    setPhase({ kind: 'uploading', fraction: 0 })
    try {
      const result = await api.importPdf(
        file,
        (f) => setPhase(f >= 1 ? { kind: 'processing' } : { kind: 'uploading', fraction: f }),
        abort.current.signal,
      )
      setPhase({ kind: 'done', result })
    } catch (err) {
      setPhase({ kind: 'error', message: (err as Error).message })
    }
  }

  return (
    <div className="import narrow">
      <PageHeader title="Import a cookbook" sub="Upload a cookbook PDF you own. Recipes you've edited in the app are never overwritten." />

      <form className="panel import-form" onSubmit={start}>
        <label className="file">
          <input type="file" accept="application/pdf,.pdf" disabled={busy} onChange={(e) => { setFile(e.target.files?.[0] ?? null); setPhase({ kind: 'idle' }) }} />
          <span className="file-face">
            <Icon name="file" size={28} />
            <span>
              <strong>{file ? file.name : 'Choose a PDF'}</strong>
              <span className="file-meta">{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : 'Single-page and two-page recipe layouts are detected automatically'}</span>
            </span>
          </span>
        </label>

        {phase.kind === 'uploading' && (
          <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(phase.fraction * 100)} aria-label="Upload progress">
            <span style={{ width: `${phase.fraction * 100}%` }} />
          </div>
        )}
        {phase.kind === 'processing' && (
          <p className="import-status"><Spinner label="Reading recipes" /> Reading recipes, photos and macros. Big books take a minute.</p>
        )}
        {phase.kind === 'error' && <p className="form-error" role="alert"><Icon name="alert" size={18} /> {phase.message}</p>}

        <div className="form-actions">
          {busy ? (
            <button type="button" className="btn" onClick={() => abort.current?.abort()}>Cancel</button>
          ) : (
            <button type="submit" className="btn btn-primary btn-lg" disabled={!file}><Icon name="upload" size={20} /> Import</button>
          )}
        </div>
      </form>

      {phase.kind === 'done' && (
        <section className="panel import-result" aria-labelledby="result-h" aria-live="polite">
          <h2 id="result-h">{phase.result.source}</h2>
          <dl className="import-counts">
            <div><dt>Added</dt><dd>{phase.result.added}</dd></div>
            <div><dt>Updated</dt><dd>{phase.result.updated}</dd></div>
            <div><dt>Kept (edited)</dt><dd>{phase.result.kept}</dd></div>
          </dl>
          {phase.result.warnings.length > 0 ? (
            <>
              <h3>Worth a quick look ({phase.result.warnings.length})</h3>
              <ul className="warnings">
                {phase.result.warnings.map((w, i) => (
                  <li key={i}>
                    <Link to={`/?q=${encodeURIComponent(w.title)}`}>{w.title}</Link> <span className="muted">page {w.page}</span>
                    <ul>{w.warnings.map((m, j) => <li key={j}>{m}</li>)}</ul>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>Everything parsed cleanly.</p>
          )}
          <Link className="btn btn-primary" to="/?sort=recent">See the recipes</Link>
        </section>
      )}

      <p className="muted import-cli">
        On the home PC you can also run <code>uv run cookbook-import path/to/Cookbook.pdf</code>.
      </p>
    </div>
  )
}
