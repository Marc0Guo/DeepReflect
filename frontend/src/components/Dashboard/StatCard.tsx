import { useEffect, useRef, useState } from 'react'

interface Props {
  label: string
  value: number | string
  sub?: string
  accentVar?: string
  icon?: React.ReactNode
}

function useCountUp(target: number, duration = 800) {
  const [current, setCurrent] = useState(0)
  const ref = useRef<number>(0)
  useEffect(() => {
    if (typeof target !== 'number') return
    const start = ref.current
    const diff = target - start
    const startTime = performance.now()
    function tick(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const val = Math.round(start + diff * (1 - Math.pow(1 - progress, 3)))
      setCurrent(val)
      ref.current = val
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration])
  return current
}

export function StatCard({ label, value, sub, accentVar = '--accent', icon }: Props) {
  const numericValue = typeof value === 'number' ? value : null
  const displayValue = numericValue !== null ? useCountUp(numericValue) : value

  return (
    <div className="glass glass-hover p-5 relative overflow-hidden cursor-default">
      <div
        className="absolute top-0 left-0 w-full h-[2px] opacity-70"
        style={{ background: `linear-gradient(90deg, var(${accentVar}), transparent 70%)` }}
      />
      <div className="flex items-start justify-between mb-3">
        <div
          className="w-9 h-9 rounded-[12px] flex items-center justify-center"
          style={{
            background: `color-mix(in srgb, var(${accentVar}) 15%, transparent)`,
            border: `1px solid color-mix(in srgb, var(${accentVar}) 25%, transparent)`,
          }}
        >
          {icon || (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={`var(${accentVar})`} strokeWidth="2" strokeLinecap="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          )}
        </div>
      </div>
      <div className="font-display text-3xl font-extrabold tracking-tight" style={{ color: `var(${accentVar})` }}>
        {displayValue}
      </div>
      <div className="section-label mt-1.5">{label}</div>
      {sub && <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-faint)' }}>{sub}</div>}
    </div>
  )
}
