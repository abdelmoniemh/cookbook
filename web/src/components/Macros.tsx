import { num } from '../lib/format'

type M = { kcal: number | null; protein: number | null; carbs: number | null; fat: number | null }

/** Big per-serving figures, plate colours as keys. */
export function MacroFigures({ m, size = 'md', caption }: { m: M; size?: 'md' | 'lg'; caption?: string }) {
  const rows: [string, string, number | null, string][] = [
    ['kcal', 'kcal', m.kcal, ''],
    ['protein', 'Protein', m.protein, 'g'],
    ['carbs', 'Carbs', m.carbs, 'g'],
    ['fat', 'Fat', m.fat, 'g'],
  ]
  return (
    <dl className={`figures figures-${size}`} aria-label={caption}>
      {rows.map(([key, label, value, unit]) => (
        <div key={key} className={`figure figure-${key}`}>
          <dt><span className="key" aria-hidden="true" />{label}</dt>
          <dd>
            {num(value)}
            {unit && value != null && <span className="unit">{unit}</span>}
          </dd>
        </div>
      ))}
    </dl>
  )
}
