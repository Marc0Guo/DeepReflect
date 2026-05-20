import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import { DashboardMetricsGrid } from '../components/Dashboard/DashboardMetricsGrid'
import { ConceptTable } from '../components/Dashboard/ConceptTable'
import {
  DashboardFilterBar,
  DEFAULT_DASHBOARD_FILTERS,
} from '../components/Dashboard/DashboardFilterBar'
import { AgentUsageCharts } from '../components/Dashboard/AgentUsageCharts'
import { BehaviorInsights } from '../components/Dashboard/BehaviorInsights'
import { ImportCursorModal } from '../components/Dashboard/ImportCursorModal'
import { RunAnalysisModal } from '../components/Dashboard/RunAnalysisModal'
import type { Concept, DashboardAnalytics, DashboardFilters, DashboardInsights, Stats } from '../types'

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)
  const [insights, setInsights] = useState<DashboardInsights | null>(null)
  const [calendarYear, setCalendarYear] = useState<number | undefined>(undefined)
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_DASHBOARD_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState<DashboardFilters>(DEFAULT_DASHBOARD_FILTERS)
  const [loading, setLoading] = useState(true)
  const [ingesting, setIngesting] = useState(false)
  const [cursorModalOpen, setCursorModalOpen] = useState(false)
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false)
  const [clearingMemory, setClearingMemory] = useState(false)
  const [importNotice, setImportNotice] = useState<string | null>(null)

  useEffect(() => {
    if (!importNotice) return
    const timer = window.setTimeout(() => setImportNotice(null), 6000)
    return () => window.clearTimeout(timer)
  }, [importNotice])

  useEffect(() => {
    const timer = window.setTimeout(() => setAppliedFilters(filters), 300)
    return () => window.clearTimeout(timer)
  }, [filters])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [s, c, a, ins] = await Promise.all([
        api.stats(appliedFilters),
        api.concepts(1, appliedFilters),
        api.dashboardAnalytics(appliedFilters),
        api.dashboardInsights(appliedFilters, calendarYear),
      ])
      setStats(s)
      setConcepts(c)
      setAnalytics(a)
      setInsights(ins)
    } catch (err) {
      console.error('Dashboard load failed', err)
    }
    setLoading(false)
  }, [appliedFilters, calendarYear])

  useEffect(() => {
    load()
  }, [load])

  const sources = stats?.available_sources ?? []

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-8 h-8 border-2 rounded-full animate-spin"
            style={{
              borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)',
              borderTopColor: 'var(--accent)',
            }}
          />
          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Loading dashboard...
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 lg:p-10 max-w-6xl mx-auto space-y-6">
      <div className="flex items-end justify-between animate-fade-in-up">
        <div>
          <h1
            className="font-display text-3xl font-extrabold tracking-tight"
            style={{ color: 'var(--text-primary)' }}
          >
            {getGreeting()}
          </h1>
          <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>
            Here's an overview of your learning journey.
          </p>
        </div>
        <div className="flex gap-2.5">
          <button
            onClick={async () => {
              setIngesting(true)
              setImportNotice(null)
              try {
                const result = await api.ingestAll()
                if (result.imported === 0) {
                  setImportNotice('No Claude Code conversations found. Install Claude Code or import a file instead.')
                } else {
                  setImportNotice(`Imported ${result.imported} Claude turns (${result.new} new).`)
                }
              } catch {
                setImportNotice('Claude import failed. Is the backend running on port 7733?')
              }
              setIngesting(false)
              load()
            }}
            disabled={ingesting}
            className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 flex items-center gap-2 cursor-pointer"
            style={{ color: 'var(--text-secondary)' }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            {ingesting ? 'Importing...' : 'Import Claude'}
          </button>
          <button
            onClick={() => {
              setImportNotice(null)
              setCursorModalOpen(true)
            }}
            className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center gap-2 cursor-pointer"
            style={{ color: 'var(--text-secondary)' }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M9 9l6 6M15 9l-6 6" />
            </svg>
            Import Cursor
          </button>
          <button
            onClick={async () => {
              if (
                !window.confirm(
                  'Clear all imported conversations, concepts, flashcards, and study content from memory? This cannot be undone.',
                )
              ) {
                return
              }
              setClearingMemory(true)
              setImportNotice(null)
              try {
                await api.clearMemory()
                setImportNotice('Memory cleared. Re-import to load conversations again.')
                load()
              } catch {
                setImportNotice('Clear memory failed. Is the backend running on port 7733?')
              }
              setClearingMemory(false)
            }}
            disabled={clearingMemory}
            className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 flex items-center gap-2 cursor-pointer"
            style={{ color: 'var(--text-secondary)' }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6M14 11v6" />
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
            </svg>
            {clearingMemory ? 'Clearing...' : 'Clear memory'}
          </button>
          <button
            onClick={() => setAnalysisModalOpen(true)}
            className="px-4 py-2.5 text-[13px] font-semibold rounded-[14px] transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center gap-2 cursor-pointer"
            style={{
              background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
              color: 'white',
              boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 30%, transparent)',
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            Run Analysis
          </button>
        </div>
      </div>

      {importNotice && (
        <div
          className="glass-subtle px-4 py-3 text-sm animate-fade-in-up"
          style={{ color: 'var(--text-secondary)', borderLeft: '3px solid var(--accent)' }}
        >
          {importNotice}
        </div>
      )}

      {stats && (
        <div className={`animate-fade-in-up ${loading ? 'opacity-60' : ''}`}>
          <DashboardMetricsGrid stats={stats} />
        </div>
      )}

      <DashboardFilterBar
        filters={filters}
        sources={sources}
        onChange={setFilters}
        onClear={() => {
          setFilters(DEFAULT_DASHBOARD_FILTERS)
          setAppliedFilters(DEFAULT_DASHBOARD_FILTERS)
        }}
      />

      <div className={loading ? 'opacity-60' : ''}>
        <AgentUsageCharts data={analytics} period={appliedFilters.period} />
      </div>

      <div className={loading ? 'opacity-60' : ''}>
        <BehaviorInsights
          data={insights}
          sourceFilter={appliedFilters.source}
          calendarYear={calendarYear ?? insights?.calendar_year ?? new Date().getFullYear()}
          onCalendarYearChange={setCalendarYear}
        />
      </div>

      {stats && Object.keys(stats.sources).length > 0 && (
        <div className={`glass p-6 animate-fade-in-up stagger-6 ${loading ? 'opacity-60' : ''}`}>
          <div className="section-label mb-4">
            {stats.filters_active ? 'Sources in Filter' : 'AI Tools Used'}
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.sources).map(([src, cnt]) => (
              <span
                key={src}
                className="glass-subtle text-xs px-3.5 py-1.5 font-medium flex items-center gap-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                {src}
                <span className="font-bold tabular-nums" style={{ color: 'var(--accent)' }}>
                  {cnt}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className={`glass p-6 animate-fade-in-up stagger-7 ${loading ? 'opacity-60' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="section-label">
            {stats?.filters_active ? 'Filtered Concepts' : 'Top Concepts'}
          </div>
          <span className="text-[11px] tabular-nums" style={{ color: 'var(--text-faint)' }}>
            {concepts.length} tracked
          </span>
        </div>
        <ConceptTable concepts={concepts.slice(0, 20)} />
      </div>

      <ImportCursorModal
        open={cursorModalOpen}
        onClose={() => setCursorModalOpen(false)}
        onComplete={(result) => {
          if (result) {
            if (result.imported === 0) {
              setImportNotice('No Cursor conversations found in local storage.')
            } else {
              setImportNotice(`Imported ${result.imported} Cursor turns (${result.new} new).`)
            }
            load()
          }
        }}
      />

      <RunAnalysisModal
        open={analysisModalOpen}
        onClose={() => setAnalysisModalOpen(false)}
        onComplete={(result) => {
          if (result) {
            setImportNotice(
              `Analyzed ${result.processed} messages${result.errors > 0 ? ` (${result.errors} failed)` : ''}. ${result.remaining} still unanalyzed.`,
            )
            load()
          }
        }}
      />
    </div>
  )
}
