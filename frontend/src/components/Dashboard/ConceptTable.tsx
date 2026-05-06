import type { Concept } from '../../types'

interface Props {
  concepts: Concept[]
  onSelect?: (c: Concept) => void
}

const CAT_COLORS: Record<string, string> = {
  python: '--accent', ml: '--accent-secondary', git: '--accent-warm',
  web: '--accent-green', data: '--accent', math: '--accent-warm',
  general: '--text-muted', other: '--text-muted',
}

export function ConceptTable({ concepts, onSelect }: Props) {
  if (!concepts.length) {
    return (
      <div className="text-center py-12">
        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>No concepts tracked yet.</div>
        <div className="text-xs mt-1" style={{ color: 'var(--text-faint)' }}>Import and analyze conversations to get started.</div>
      </div>
    )
  }

  const maxCount = concepts[0]?.ask_count ?? 1

  return (
    <div className="space-y-0.5">
      <div className="grid grid-cols-[1fr_auto_auto_110px] gap-3 px-3 py-2 section-label">
        <span>Concept</span><span>Category</span><span>Status</span><span className="text-right">Frequency</span>
      </div>
      {concepts.map((c, i) => {
        const catVar = CAT_COLORS[c.category] ?? '--text-muted'
        return (
          <div
            key={c.id}
            onClick={() => onSelect?.(c)}
            className={`grid grid-cols-[1fr_auto_auto_110px] gap-3 items-center py-3 px-3 rounded-[14px] transition-all duration-200 animate-fade-in-up group ${onSelect ? 'cursor-pointer' : ''}`}
            style={{ animationDelay: `${i * 30}ms`, ...(onSelect ? {} : {}) }}
            onMouseEnter={(e) => { if (onSelect) (e.currentTarget as HTMLElement).style.background = 'var(--surface-raised)' }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = '' }}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: `var(${catVar})` }} />
              <span className="text-[13px] font-medium truncate" style={{ color: 'var(--text-secondary)' }}>{c.name}</span>
            </div>
            <span
              className="text-[10px] font-semibold px-2.5 py-1 rounded-lg"
              style={{ background: `color-mix(in srgb, var(${catVar}) 12%, transparent)`, color: `var(${catVar})` }}
            >
              {c.category}
            </span>
            {c.weak_score >= 0.4 ? (
              <span className="text-[10px] font-semibold px-2.5 py-1 rounded-lg" style={{ background: 'color-mix(in srgb, var(--accent-pink) 12%, transparent)', color: 'var(--accent-pink)' }}>needs review</span>
            ) : (
              <span className="text-[10px] font-semibold px-2.5 py-1 rounded-lg" style={{ background: 'color-mix(in srgb, var(--accent-green) 12%, transparent)', color: 'var(--accent-green)' }}>on track</span>
            )}
            <div className="w-full">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'var(--surface-raised)' }}>
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(c.ask_count / maxCount) * 100}%`, background: `linear-gradient(90deg, var(--accent), var(--accent-secondary))` }} />
                </div>
                <span className="text-[10px] tabular-nums w-6 text-right" style={{ color: 'var(--text-faint)' }}>{c.ask_count}x</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
