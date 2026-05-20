import { MiniStatCard } from './MiniStatCard'
import type { Stats } from '../../types'

function formatLastUpdated(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTokenCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function formatDuration(seconds: number): string {
  if (seconds <= 0) return '0m'
  const h = Math.floor(seconds / 3600)
  const m = Math.round((seconds % 3600) / 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

interface Props {
  stats: Stats
}

export function DashboardMetricsGrid({ stats }: Props) {
  const dateRange =
    stats.history_start && stats.history_end
      ? `${formatShortDate(stats.history_start)} – ${formatShortDate(stats.history_end)}`
      : 'No history in current filter'

  const categoryValue = stats.category_count == null ? 'N/A' : String(stats.category_count)

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <MiniStatCard
        label="Last updated"
        value={formatLastUpdated(stats.last_updated)}
        tooltip="Most recent exchange timestamp within the active dashboard filters."
        accentVar="--accent"
      />
      <MiniStatCard
        label="Coverage"
        value={stats.coverage_days ?? 0}
        tooltip={`Calendar days from earliest to latest exchange. ${dateRange}`}
        accentVar="--accent-secondary"
      />
      <MiniStatCard
        label="Longest streak"
        value={`${stats.longest_streak_days ?? 0}d`}
        tooltip="Longest run of consecutive calendar days with at least one exchange in the filter."
        accentVar="--accent-warm"
      />
      <MiniStatCard
        label="Total time"
        value={formatDuration(stats.total_duration_seconds ?? 0)}
        tooltip="Estimated active time from session gaps (30 min cap between turns, 5 min minimum per segment)."
        accentVar="--accent-pink"
      />
      <MiniStatCard
        label="Categories"
        value={categoryValue}
        tooltip={
          stats.category_count == null
            ? 'Run Analysis to tag concepts and populate category buckets. Shows N/A until then.'
            : 'Count of distinct concept categories linked to exchanges in the current filter.'
        }
        accentVar="--accent"
      />
      <MiniStatCard
        label="Token usage"
        value={formatTokenCount(stats.filtered_tokens ?? 0)}
        tooltip={
          stats.filters_active
            ? 'Estimated tokens (prompt + response ÷ 4 chars) for exchanges matching current filters. Not from provider billing.'
            : 'Estimated total tokens across all imported prompts and responses. Not from provider billing.'
        }
        accentVar="--accent-secondary"
      />
    </div>
  )
}
