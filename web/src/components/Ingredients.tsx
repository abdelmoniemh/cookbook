import type { Ingredient, IngredientGroup } from '../api/types'
import { Icon } from './Icon'

type Props = {
  groups: IngredientGroup[]
  checked?: Set<number>
  onToggle?: (id: number) => void
}

/** Ingredient groups. Note lines (instructions mixed into the list) are set apart from things to buy. */
export function IngredientGroups({ groups, checked, onToggle }: Props) {
  return (
    <div className="ing-groups">
      {groups.map((g, gi) => (
        <div className="ing-group" key={gi}>
          {g.name && <h3 className="ing-group-name">{g.name}</h3>}
          {g.note && <p className="ing-note">{g.note}</p>}
          <ul className="ing-list">
            {g.items.map((it) =>
              it.kind === 'note' ? (
                <li key={it.id} className="ing-note">{it.raw}</li>
              ) : onToggle ? (
                <li key={it.id}>
                  <button type="button" role="checkbox" aria-checked={checked?.has(it.id) ?? false} className="ing-check" onClick={() => onToggle(it.id)}>
                    <span className="tick" aria-hidden="true"><Icon name="check" size={16} /></span>
                    <IngredientText it={it} />
                  </button>
                </li>
              ) : (
                <li key={it.id} className="ing-item"><IngredientText it={it} /></li>
              ),
            )}
          </ul>
        </div>
      ))}
    </div>
  )
}

const AMOUNT = /^([\d.,/½¼¾–-]+(?:\s*(?:g|kg|ml|l|oz|lb|tsp|tbsp|cups?|scoops?|cloves?|slices?|pinch(?:es)?|handfuls?|cans?|packs?|pieces?|servings?)\b\.?)?)\s+(.+)$/i

/** Splits `display` into amount and name where the amount is a leading number, so the amount can be set in bold numerals. */
function IngredientText({ it }: { it: Ingredient }) {
  const m = it.qty != null ? it.display.match(AMOUNT) : null
  const [amount, rest] = m ? [m[1], m[2]] : [null, it.display]
  return (
    <span className="ing-text" title={it.raw !== it.display ? `Book: ${it.raw}` : undefined}>
      {amount && <span className="ing-amount">{amount}</span>}
      <span className="ing-name">{rest}</span>
      {it.alt_measure && <span className="ing-alt"> ({it.alt_measure})</span>}
      {it.note && <span className="ing-aside">{it.note}</span>}
    </span>
  )
}
