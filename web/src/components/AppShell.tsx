import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Icon, PlateMark, type IconName } from './Icon'

const TABS: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: '/', label: 'Browse', icon: 'browse', end: true },
  { to: '/plan', label: 'Plan', icon: 'plan' },
  { to: '/shopping', label: 'Shopping', icon: 'basket' },
  { to: '/new', label: 'Add', icon: 'plus' },
]

export function AppShell() {
  const { pathname } = useLocation()
  const browseActive = pathname === '/' || (pathname.startsWith('/r/') && !pathname.endsWith('/edit'))
  return (
    <div className="app">
      <a className="skip" href="#main">Skip to content</a>
      <header className="topbar">
        <NavLink to="/" className="brand" aria-label="Cookbook home">
          <PlateMark size={28} />
          <span>Cookbook</span>
        </NavLink>
        <nav className="topnav" aria-label="Main">
          {TABS.slice(0, 3).map((t) => (
            <NavLink key={t.to} to={t.to} end={t.end} className={({ isActive }) => (isActive || (t.to === '/' && browseActive) ? 'active' : '')}>
              {t.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-end">
          <NavLink to="/import" className="topbar-link">Import PDF</NavLink>
          <NavLink to="/new" className="btn btn-on-shell">
            <Icon name="plus" size={18} /> New recipe
          </NavLink>
        </div>
      </header>
      <main id="main" className="main" tabIndex={-1}>
        <Outlet />
      </main>
      <nav className="tabbar" aria-label="Main">
        {TABS.map((t) => (
          <NavLink key={t.to} to={t.to} end={t.end} className={({ isActive }) => (isActive || (t.to === '/' && browseActive) ? 'active' : '')}>
            <Icon name={t.icon} size={24} />
            <span>{t.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

export function PageHeader({ title, sub, actions, back }: { title: string; sub?: React.ReactNode; actions?: React.ReactNode; back?: React.ReactNode }) {
  return (
    <div className="pagehead">
      {back}
      <div className="pagehead-text">
        <h1>{title}</h1>
        {sub && <p className="pagehead-sub">{sub}</p>}
      </div>
      {actions && <div className="pagehead-actions">{actions}</div>}
    </div>
  )
}
