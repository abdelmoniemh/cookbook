import { Link } from 'react-router-dom'
import { EmptyState } from '../components/States'

export function NotFound() {
  return (
    <EmptyState title="Page not found" action={<Link className="btn btn-primary" to="/">Back to recipes</Link>}>
      <p>That address doesn't match anything in the cookbook.</p>
    </EmptyState>
  )
}
