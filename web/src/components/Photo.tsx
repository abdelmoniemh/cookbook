import { useState } from 'react'
import { PlateMark } from './Icon'

/** Recipe photo with a quiet placeholder while loading and when there is no image. */
export function Photo({ src, alt, className = '', eager = false }: { src: string | null; alt: string; className?: string; eager?: boolean }) {
  const [state, setState] = useState<'loading' | 'ok' | 'error'>(src ? 'loading' : 'error')
  return (
    <div className={`photo ${className} photo-${state}`}>
      {src && state !== 'error' && (
        <img
          src={src}
          alt={alt}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          onLoad={() => setState('ok')}
          onError={() => setState('error')}
        />
      )}
      {state === 'error' && <span className="photo-none"><PlateMark size={36} /></span>}
    </div>
  )
}
