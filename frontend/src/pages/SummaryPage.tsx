import { useState } from 'react'
import { api } from '../api/client'
import type { Period } from '../types'

const PERIODS: { value: Period; label: string; desc: string; icon: React.ReactNode }[] = [
  {
    value: 'daily', label: 'Today', desc: "What you've explored today",
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>,
  },
  {
    value: 'weekly', label: 'This Week', desc: '7-day learning snapshot',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>,
  },
  {
    value: 'monthly', label: 'This Month', desc: 'Monthly progress report',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>,
  },
  {
    value: 'yearly', label: 'This Year', desc: 'Year in review',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>,
  },
]

export function SummaryPage() {
  const [selected, setSelected] = useState<Period>('weekly')
  const [loading, setLoading] = useState(false)
  const [roasting, setRoasting] = useState(false)

  async function generate() {
    setLoading(true)
    const url = `${api.generateSummary(selected)}?t=${Date.now()}`
    window.open(url, '_blank')
    setLoading(false)
  }

  async function roast() {
    setRoasting(true)
    window.open(`/api/summary/roast?t=${Date.now()}`, '_blank')
    // Brief delay so button feels responsive
    setTimeout(() => setRoasting(false), 1500)
  }

  return (
    <div className="p-8 lg:p-10 max-w-3xl mx-auto space-y-8">
      <div className="animate-fade-in-up">
        <h1 className="font-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>Summaries</h1>
        <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>Generate shareable, cinematic reports of your learning journey.</p>
      </div>

      {/* ROAST CARD */}
      <div className="glass p-6 animate-fade-in-up stagger-1 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: 'linear-gradient(90deg, var(--accent-secondary), var(--accent), transparent)' }} />
        <div className="flex items-start gap-4">
          <div
            className="w-9 h-9 rounded-[12px] shrink-0 flex items-center justify-center"
            style={{ background: 'color-mix(in srgb, var(--accent-secondary) 12%, transparent)', border: '1px solid color-mix(in srgb, var(--accent-secondary) 20%, transparent)' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2"/><path d="M12 8v4l3 3"/></svg>
          </div>
          <div className="flex-1">
            <div className="font-display text-base font-bold" style={{ color: 'var(--text-primary)' }}>Vibe Roast</div>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              Let DeepReflect roast your AI chat habits based on your imported Cursor / Claude history!
            </p>
          </div>
        </div>
        <button onClick={roast} disabled={roasting}
          className="w-full mt-5 py-3 text-[13px] font-semibold rounded-[14px] transition-all disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer"
          style={{ background: 'linear-gradient(135deg, var(--accent-secondary), var(--accent))', color: 'white', boxShadow: '0 4px 20px color-mix(in srgb, var(--accent-secondary) 30%, transparent)' }}>
          {roasting
            ? <><div className="w-4 h-4 border-2 rounded-full animate-spin" style={{ borderColor: 'rgba(255,255,255,.3)', borderTopColor: 'white' }} /> Generating Roast…</>
            : <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
                Open Vibe Roast
              </>
          }
        </button>
        <p className="text-[11px] mt-3 text-center" style={{ color: 'var(--text-faint)' }}>
          Requires LLM API key — configure in Settings first.
        </p>
      </div>

      {/* PERIOD SELECTOR */}
      <div className="space-y-5 animate-fade-in-up stagger-2">
        <div className="section-label">Learning Summary</div>
        <div className="grid grid-cols-2 gap-3">
          {PERIODS.map((p) => (
            <button key={p.value} onClick={() => setSelected(p.value)}
              className="text-left p-5 glass glass-hover transition-all duration-300 group cursor-pointer"
              style={{
                borderColor: selected === p.value ? 'color-mix(in srgb, var(--accent) 40%, transparent)' : undefined,
                boxShadow: selected === p.value ? '0 0 24px -6px color-mix(in srgb, var(--accent) 20%, transparent), var(--glass-inner)' : undefined,
              }}>
              <div className="mb-3 transition-colors" style={{ color: selected === p.value ? 'var(--accent)' : 'var(--text-faint)' }}>{p.icon}</div>
              <div className="font-display text-base font-bold" style={{ color: selected === p.value ? 'var(--accent)' : 'var(--text-primary)' }}>{p.label}</div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <button onClick={generate} disabled={loading}
        className="w-full py-3.5 text-[13px] font-semibold rounded-[14px] transition-all duration-300 disabled:opacity-40 flex items-center justify-center gap-2 animate-fade-in-up stagger-3 cursor-pointer"
        style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white', boxShadow: '0 4px 24px color-mix(in srgb, var(--accent) 30%, transparent)' }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
        {loading ? 'Generating...' : `Generate ${PERIODS.find((p) => p.value === selected)?.label} Summary`}
      </button>

      <p className="text-[11px] text-center animate-fade-in-up stagger-4" style={{ color: 'var(--text-faint)' }}>
        Also via CLI:{' '}
        <code className="font-mono px-1.5 py-0.5 rounded" style={{ background: 'var(--surface-raised)', color: 'color-mix(in srgb, var(--accent) 70%, var(--text-muted))' }}>deepreflect summary --period {selected}</code>
      </p>
    </div>
  )
}
