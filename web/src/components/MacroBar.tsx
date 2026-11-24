import { macroShares } from '../lib/format'

type Props = { protein: number | null; carbs: number | null; fat: number | null; size?: 'sm' | 'md' | 'lg'; className?: string }

/**
 * The loaded bar: a recipe's calories split by macro, drawn as plate-coloured segments on a bar sleeve.
 * Protein is loaded first, like the heaviest plate.
 */
export function MacroBar({ protein, carbs, fat, size = 'sm', className = '' }: Props) {
  const s = macroShares(protein, carbs, fat)
  if (!s) return <div className={`loadbar loadbar-${size} loadbar-empty ${className}`} aria-hidden="true" />
  const pct = (x: number) => Math.round(x * 100)
  return (
    <div
      className={`loadbar loadbar-${size} ${className}`}
      role="img"
      aria-label={`Calories from protein ${pct(s.protein)}%, carbs ${pct(s.carbs)}%, fat ${pct(s.fat)}%`}
    >
      <span className="loadbar-collar" />
      <span className="loadbar-seg seg-protein" style={{ flexGrow: s.protein }} />
      <span className="loadbar-seg seg-carbs" style={{ flexGrow: s.carbs }} />
      <span className="loadbar-seg seg-fat" style={{ flexGrow: s.fat }} />
      <span className="loadbar-collar" />
    </div>
  )
}
