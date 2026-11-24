import type { Day } from '../api/types'

export const DAYS: { id: Day; short: string; long: string }[] = [
  { id: 'mon', short: 'Mon', long: 'Monday' },
  { id: 'tue', short: 'Tue', long: 'Tuesday' },
  { id: 'wed', short: 'Wed', long: 'Wednesday' },
  { id: 'thu', short: 'Thu', long: 'Thursday' },
  { id: 'fri', short: 'Fri', long: 'Friday' },
  { id: 'sat', short: 'Sat', long: 'Saturday' },
  { id: 'sun', short: 'Sun', long: 'Sunday' },
]

function parseIso(iso: string) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}
function toIso(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function mondayOf(date = new Date()) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7))
  return toIso(d)
}

export function shiftWeek(iso: string, weeks: number) {
  const d = parseIso(iso)
  d.setDate(d.getDate() + weeks * 7)
  return toIso(d)
}

export function weekLabel(iso: string) {
  const start = parseIso(iso)
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  const sameMonth = start.getMonth() === end.getMonth()
  const f = (d: Date, opts: Intl.DateTimeFormatOptions) => d.toLocaleDateString(undefined, opts)
  const m = (d: Date) => f(d, { month: 'short' })
  return sameMonth
    ? `${start.getDate()}–${end.getDate()} ${m(end)}`
    : `${start.getDate()} ${m(start)} – ${end.getDate()} ${m(end)}`
}

export function relativeWeek(iso: string) {
  const now = mondayOf()
  if (iso === now) return 'This week'
  if (iso === shiftWeek(now, 1)) return 'Next week'
  if (iso === shiftWeek(now, -1)) return 'Last week'
  return 'Week of'
}
