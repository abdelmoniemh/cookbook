import { Icon } from './Icon'

type Props = {
  value: number
  onChange: (n: number) => void
  min?: number
  max?: number
  step?: number
  label: string
  size?: 'md' | 'lg'
  suffix?: string
}

export function Stepper({ value, onChange, min = 1, max = 99, step = 1, label, size = 'md', suffix }: Props) {
  const set = (n: number) => onChange(Math.min(max, Math.max(min, Math.round(n * 100) / 100)))
  return (
    <div className={`stepper stepper-${size}`} role="group" aria-label={label}>
      <button type="button" onClick={() => set(value - step)} disabled={value <= min} aria-label={`Fewer ${label.toLowerCase()}`}>
        <Icon name="minus" size={20} />
      </button>
      <output aria-live="polite">
        <span className="stepper-value">{value}</span>
        {suffix && <span className="stepper-suffix">{suffix}</span>}
      </output>
      <button type="button" onClick={() => set(value + step)} disabled={value >= max} aria-label={`More ${label.toLowerCase()}`}>
        <Icon name="plus" size={20} />
      </button>
    </div>
  )
}
