import type { DashboardFilters, DashboardPeriod, DashboardStatus } from '../../types'

const PERIODS: { value: DashboardPeriod; label: string }[] = [
  { value: 'all', label: 'All time' },
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'This week' },
  { value: 'month', label: 'This month' },
  { value: 'year', label: 'This year' },
]

const STATUSES: { value: DashboardStatus; label: string }[] = [
  { value: 'all', label: 'All concepts' },
  { value: 'weak', label: 'Needs review' },
  { value: 'solved', label: 'On track' },
]

interface Props {
  filters: DashboardFilters
  sources: string[]
  onChange: (filters: DashboardFilters) => void
  onClear: () => void
}

export function DashboardFilterBar({ filters, sources, onChange, onClear }: Props) {
  const active =
    filters.period !== 'all' ||
    filters.source !== '' ||
    filters.concept.trim() !== '' ||
    filters.status !== 'all'

  function patch(partial: Partial<DashboardFilters>) {
    onChange({ ...filters, ...partial })
  }

  return (
    <div className="filter-bar-panel p-5 animate-fade-in-up stagger-1 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="section-label" style={{ color: 'var(--filter-label)' }}>
          Filters
        </div>
        {active && (
          <button
            type="button"
            onClick={onClear}
            className="text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
            style={{ color: 'var(--accent)' }}
          >
            Clear all
          </button>
        )}
      </div>

      <div className="filter-grid">
        <label className="filter-field">
          <span className="filter-label">Period</span>
          <select
            value={filters.period}
            onChange={(e) => patch({ period: e.target.value as DashboardPeriod })}
            className="filter-control"
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span className="filter-label">Source</span>
          <select
            value={filters.source}
            onChange={(e) => patch({ source: e.target.value })}
            className="filter-control"
          >
            <option value="">All sources</option>
            {sources.map((src) => (
              <option key={src} value={src}>
                {src}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span className="filter-label">Topic</span>
          <input
            type="search"
            value={filters.concept}
            onChange={(e) => patch({ concept: e.target.value })}
            placeholder="Search concepts..."
            className="filter-control"
          />
        </label>

        <label className="filter-field">
          <span className="filter-label">Status</span>
          <select
            value={filters.status}
            onChange={(e) => patch({ status: e.target.value as DashboardStatus })}
            className="filter-control"
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}

export const DEFAULT_DASHBOARD_FILTERS: DashboardFilters = {
  period: 'all',
  source: '',
  concept: '',
  status: 'all',
}

export function periodLabel(period: DashboardPeriod): string {
  return PERIODS.find((p) => p.value === period)?.label ?? 'This week'
}
