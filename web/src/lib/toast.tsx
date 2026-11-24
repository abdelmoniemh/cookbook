import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Toast = { id: number; text: string; tone?: 'error'; link?: { to: string; label: string } }
type Ctx = (t: Omit<Toast, 'id'>) => void

const ToastContext = createContext<Ctx>(() => {})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const id = useRef(0)
  const push = useCallback<Ctx>((t) => {
    const tid = ++id.current
    setToasts((all) => [...all.slice(-2), { ...t, id: tid }])
    window.setTimeout(() => setToasts((all) => all.filter((x) => x.id !== tid)), t.tone === 'error' ? 6000 : 3500)
  }, [])
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast${t.tone === 'error' ? ' toast-error' : ''}`}>
            <span>{t.text}</span>
            {t.link && <Link to={t.link.to}>{t.link.label}</Link>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
