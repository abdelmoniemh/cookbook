import type { ReactNode } from 'react'
import { Icon } from './Icon'

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <Icon name="alert" size={28} />
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      {onRetry && <button type="button" className="btn" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="state">
      <h2>{title}</h2>
      {children}
      {action && <div className="state-actions">{action}</div>}
    </div>
  )
}

export function CardSkeletons({ count = 8 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card card-skeleton" aria-hidden="true">
          <div className="photo skel" />
          <div className="skel skel-line" />
          <div className="skel skel-line short" />
        </div>
      ))}
    </>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return <span className="spinner" role="status" aria-label={label} />
}
