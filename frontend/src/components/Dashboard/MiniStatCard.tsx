interface Props {
  label: string
  value: string | number
  tooltip?: string
  accentVar?: string
}

export function MiniStatCard({ label, value, tooltip, accentVar = '--accent' }: Props) {
  return (
    <div
      className="glass glass-hover p-3.5 relative overflow-hidden cursor-default min-w-0"
      title={tooltip}
    >
      <div
        className="absolute top-0 left-0 w-full h-[2px] opacity-60"
        style={{ background: `linear-gradient(90deg, var(${accentVar}), transparent 70%)` }}
      />
      <div
        className="font-display text-xl font-extrabold tracking-tight truncate tabular-nums"
        style={{ color: `var(${accentVar})` }}
      >
        {value}
      </div>
      <div
        className="text-[10px] font-semibold uppercase tracking-wider mt-1.5 leading-tight truncate"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </div>
    </div>
  )
}

