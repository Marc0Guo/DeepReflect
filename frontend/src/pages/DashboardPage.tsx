import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { StatCard } from '../components/Dashboard/StatCard'
import { ConceptTable } from '../components/Dashboard/ConceptTable'
import type { Concept, Stats } from '../types'

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [ingestingCursor, setIngestingCursor] = useState(false)

  async function load() {
    setLoading(true)
    try { const [s, c] = await Promise.all([api.stats(), api.concepts(1)]); setStats(s); setConcepts(c) } catch (_) {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />
          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading dashboard...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 lg:p-10 max-w-6xl mx-auto space-y-6">
      <div className="flex items-end justify-between animate-fade-in-up">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>{getGreeting()}</h1>
          <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>Here's an overview of your learning journey.</p>
        </div>
        <div className="flex gap-2.5">
          <button onClick={async () => { setIngesting(true); try { await api.ingestAll() } catch {} setIngesting(false); load() }} disabled={ingesting} className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 flex items-center gap-2 cursor-pointer" style={{ color: 'var(--text-secondary)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            {ingesting ? 'Importing...' : 'Import Claude'}
          </button>
          <button onClick={async () => { setIngestingCursor(true); try { await api.ingestCursor() } catch {} setIngestingCursor(false); load() }} disabled={ingestingCursor} className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 flex items-center gap-2 cursor-pointer" style={{ color: 'var(--text-secondary)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9l6 6M15 9l-6 6"/></svg>
            {ingestingCursor ? 'Importing...' : 'Import Cursor'}
          </button>
          <button onClick={async () => { setAnalyzing(true); try { await api.analyze(100) } catch {} setAnalyzing(false); load() }} disabled={analyzing} className="px-4 py-2.5 text-[13px] font-semibold rounded-[14px] transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 flex items-center gap-2 cursor-pointer" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white', boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 30%, transparent)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            {analyzing ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="animate-fade-in-up stagger-1">
            <StatCard label="Total Exchanges" value={stats.total_turns} accentVar="--accent"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>} />
          </div>
          <div className="animate-fade-in-up stagger-2">
            <StatCard label="This Week" value={stats.weekly_turns} accentVar="--accent-secondary"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>} />
          </div>
          <div className="animate-fade-in-up stagger-3">
            <StatCard label="Concepts Tracked" value={stats.total_concepts} accentVar="--accent-warm"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-warm)" strokeWidth="2" strokeLinecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>} />
          </div>
          <div className="animate-fade-in-up stagger-4">
            <StatCard label="Flashcards" value={stats.total_flashcards} accentVar="--accent-pink"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-pink)" strokeWidth="2" strokeLinecap="round"><rect x="2" y="6" width="16" height="14" rx="2"/><path d="M6 2h12a2 2 0 0 1 2 2v12"/></svg>} />
          </div>
        </div>
      )}

      {stats && Object.keys(stats.sources).length > 0 && (
        <div className="glass p-6 animate-fade-in-up stagger-5">
          <div className="section-label mb-4">AI Tools Used</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.sources).map(([src, cnt]) => (
              <span key={src} className="glass-subtle text-xs px-3.5 py-1.5 font-medium flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}>
                {src}
                <span className="font-bold tabular-nums" style={{ color: 'var(--accent)' }}>{cnt}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="glass p-6 animate-fade-in-up stagger-6">
        <div className="flex items-center justify-between mb-4">
          <div className="section-label">Top Concepts</div>
          <span className="text-[11px] tabular-nums" style={{ color: 'var(--text-faint)' }}>{concepts.length} tracked</span>
        </div>
        <ConceptTable concepts={concepts.slice(0, 20)} />
      </div>
    </div>
  )
}
