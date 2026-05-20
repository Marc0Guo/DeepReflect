import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { periodLabel } from './DashboardFilterBar'
import type { DashboardAnalytics, DashboardPeriod } from '../../types'

function formatDayLabel(date: string) {
  const d = new Date(`${date}T12:00:00`)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const chartAxis = { fill: 'var(--text-faint)', fontSize: 11 }
const chartGrid = { stroke: 'var(--border-divider)', strokeDasharray: '3 3' }

function ActivityTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { value: number }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="px-3 py-2 rounded-[10px] text-[12px]"
      style={{
        background: 'var(--glass-strong)',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--glass-shadow)',
      }}
    >
      <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
        {label}
      </div>
      <div style={{ color: 'var(--text-muted)' }}>
        <span className="font-bold tabular-nums" style={{ color: 'var(--accent)' }}>
          {payload[0].value}
        </span>{' '}
        exchanges
      </div>
    </div>
  )
}

function NameTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { payload?: { name: string; count: number } }[]
}) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  if (!row) return null
  return (
    <div
      className="px-3 py-2 rounded-[10px] text-[12px]"
      style={{
        background: 'var(--glass-strong)',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--glass-shadow)',
        color: 'var(--text-secondary)',
      }}
    >
      <div className="font-semibold truncate max-w-[200px]" style={{ color: 'var(--text-primary)' }}>
        {row.name}
      </div>
      <div className="tabular-nums" style={{ color: 'var(--accent)' }}>
        {row.count} mentions
      </div>
    </div>
  )
}

export function AgentUsageCharts({
  data,
  period,
}: {
  data: DashboardAnalytics | null
  period: DashboardPeriod
}) {
  if (!data) return null

  const activityData = data.activity.map((p) => ({
    ...p,
    label: formatDayLabel(p.date),
  }))
  const hasActivity = activityData.some((p) => p.count > 0)
  const topicData = data.topics.map((t) => ({ ...t, name: t.name }))
  const categoryData = data.categories

  const activitySubtitle =
    period === 'day'
      ? 'Today · exchanges per day'
      : `${periodLabel(period)} · ${data.days} day${data.days === 1 ? '' : 's'} · exchanges per day`

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      {/* Activity timeline — like timeline-for-agent trend bar, for exchanges per day */}
      <div className="glass p-6 xl:col-span-2">
        <div className="flex items-baseline justify-between mb-4">
          <div className="section-label">Agent Activity</div>
          <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>
            {activitySubtitle}
          </span>
        </div>
        {!hasActivity ? (
          <p className="text-sm text-center py-12" style={{ color: 'var(--text-faint)' }}>
            No exchanges in this range. Import conversations or widen filters.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={activityData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid {...chartGrid} vertical={false} />
              <XAxis
                dataKey="label"
                tick={chartAxis}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
                minTickGap={28}
              />
              <YAxis tick={chartAxis} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<ActivityTooltip />} />
              <Area
                type="monotone"
                dataKey="count"
                stroke="var(--accent)"
                strokeWidth={2}
                fill="url(#activityFill)"
                dot={false}
                activeDot={{ r: 4, fill: 'var(--accent)' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Topic distribution — horizontal bar (top concepts) */}
      <div className="glass p-6">
        <div className="section-label mb-4">Topic Distribution</div>
        {topicData.length === 0 ? (
          <p className="text-sm text-center py-10" style={{ color: 'var(--text-faint)' }}>
            Run analysis to extract topics from conversations.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, topicData.length * 32)}>
            <BarChart data={topicData} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 0 }}>
              <CartesianGrid {...chartGrid} horizontal={false} />
              <XAxis type="number" tick={chartAxis} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                tick={chartAxis}
                axisLine={false}
                tickLine={false}
                width={100}
              />
              <Tooltip content={<NameTooltip />} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={18}>
                {topicData.map((entry, i) => (
                  <Cell
                    key={entry.name}
                    fill={
                      i === 0
                        ? 'var(--accent)'
                        : `color-mix(in srgb, var(--accent) ${Math.max(35, 90 - i * 8)}%, var(--accent-secondary))`
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Category distribution — donut like timeline-for-agent pie */}
      <div className="glass p-6">
        <div className="section-label mb-4">By Category</div>
        {categoryData.length === 0 ? (
          <p className="text-sm text-center py-10" style={{ color: 'var(--text-faint)' }}>
            No categories yet.
          </p>
        ) : (
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={88}
                  paddingAngle={2}
                  onMouseDown={(e) => {
                    const t = e?.target
                    if (t instanceof SVGElement) t.blur()
                  }}
                >
                  {categoryData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip content={<NameTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex-1 space-y-2 w-full sm:max-w-[180px]">
              {categoryData.map((c) => (
                <li key={c.name} className="flex items-center gap-2 text-[12px]">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: c.color }}
                  />
                  <span className="capitalize truncate flex-1" style={{ color: 'var(--text-secondary)' }}>
                    {c.name}
                  </span>
                  <span className="font-semibold tabular-nums" style={{ color: 'var(--text-muted)' }}>
                    {c.count}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
