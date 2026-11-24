import { Link } from 'react-router-dom'
import type { RecipeSummary } from '../api/types'
import { num } from '../lib/format'
import { Icon } from './Icon'
import { MacroBar } from './MacroBar'
import { Photo } from './Photo'

type Props = {
  recipe: RecipeSummary
  onFavourite?: (r: RecipeSummary) => void
  onAdd?: (r: RecipeSummary) => void
  added?: boolean
  priority?: boolean
}

export function RecipeCard({ recipe: r, onFavourite, onAdd, added, priority }: Props) {
  return (
    <article className="card">
      <Link to={`/r/${r.slug}`} className="card-link">
        <Photo src={r.image_url} alt="" className="card-photo" eager={priority} />
        <h3 className="card-title">{r.title}</h3>
      </Link>
      <div className="card-meta">
        <p className="card-protein">
          <strong>{num(r.protein)}</strong><span className="unit">g</span> <span className="lbl">protein</span>
        </p>
        <p className="card-kcal"><strong>{num(r.kcal)}</strong> <span className="lbl">kcal</span></p>
      </div>
      <MacroBar protein={r.protein} carbs={r.carbs} fat={r.fat} />
      {onFavourite && (
        <button
          type="button"
          className={`card-fav${r.favourite ? ' is-on' : ''}`}
          aria-pressed={r.favourite}
          aria-label={r.favourite ? `Remove ${r.title} from favourites` : `Add ${r.title} to favourites`}
          onClick={() => onFavourite(r)}
        >
          <Icon name="heart" size={20} filled={r.favourite} />
        </button>
      )}
      {onAdd && (
        <button
          type="button"
          className={`card-add${added ? ' is-added' : ''}`}
          onClick={() => onAdd(r)}
          aria-label={added ? `${r.title} is in the plan; add again` : `Add ${r.title} to the plan`}
        >
          <Icon name={added ? 'check' : 'plus'} size={18} />
          <span>{added ? 'In plan' : 'Add'}</span>
        </button>
      )}
    </article>
  )
}
