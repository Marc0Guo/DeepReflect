import { useMemo } from 'react'
import type { CalendarDay, DashboardInsights } from '../../types'

const DOW_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const EMPTY_CELL_BG = 'color-mix(in srgb, var(--text-faint) 14%, var(--surface-raised))'

type CalDay = CalendarDay

function formatDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function intensityColor(ratio: number, cssVar: string) {
  if (ratio <= 0) return EMPTY_CELL_BG
  const pct = Math.max(28, Math.min(100, Math.round(ratio * 100)))
  return `color-mix(in srgb, var(${cssVar}) ${pct}%, var(--surface-raised))`
}

function YearFilter({
  years,
  selected,
  onChange,
}: {
  years: number[]
  selected: number
  onChange: (y: number) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {[...years].reverse().map((y) => (
        <button
          key={y}
          type="button"
          onClick={() => onChange(y)}
          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold tabular-nums transition-all cursor-pointer"
          style={
            y === selected
              ? {
                  background: 'var(--accent)',
                  color: '#fff',
                }
              : {
                  background: 'var(--surface-raised)',
                  color: 'var(--text-muted)',
                }
          }
        >
          {y}
        </button>
      ))}
    </div>
  )
}

function CalendarHeatmap({
  days = [],
  max = 0,
  year,
  sourceFilter,
}: {
  days?: CalDay[]
  max?: number
  year: number
  sourceFilter: string
}) {
  const { weeks, monthLabels } = useMemo(() => {
    const map = new Map(days.map((d) => [d.date, d]))
    const start = new Date(year, 0, 1)
    start.setDate(start.getDate() - start.getDay())
    const end = new Date(year, 11, 31)
    const grid: CalDay[][] = []
    const labels: string[] = []
    let cursor = new Date(start)
    let lastMonth = -1
    while (cursor <= end || grid.length < 53) {
      if (grid.length >= 54) break
      const week: CalDay[] = []
      for (let i = 0; i < 7; i++) {
        const key = formatDateKey(cursor)
        const inYear = cursor.getFullYear() === year
        week.push(
          inYear
            ? map.get(key) ?? { date: key, count: 0, cursor: 0, claude: 0 }
            : { date: key, count: 0, cursor: 0, claude: 0 },
        )
        if (i === 0) {
          const m = cursor.getMonth()
          if (m !== lastMonth && inYear) {
            labels.push(cursor.toLocaleDateString(undefined, { month: 'short' }))
            lastMonth = m
          } else {
            labels.push('')
          }
        }
        cursor.setDate(cursor.getDate() + 1)
      }
      grid.push(week)
      if (cursor > end && cursor.getDay() === 0) break
    }
    return { weeks: grid, monthLabels: labels }
  }, [days, year])

  if (!days.length) {
    return (
      <p className="text-sm text-center py-10" style={{ color: 'var(--text-faint)' }}>
        No activity in {year}.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto pb-2">
      <div className="flex gap-[3px] min-w-max">
        <div className="flex flex-col gap-[3px] pr-1 pt-5">
          {DOW_LABELS.map((d, i) => (
            <div
              key={d}
              className="h-[12px] text-[9px] leading-[12px]"
              style={{ color: 'var(--text-faint)', visibility: i % 2 === 0 ? 'visible' : 'hidden' }}
            >
              {d}
            </div>
          ))}
        </div>
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            <div className="h-4 text-[9px] truncate" style={{ color: 'var(--text-faint)' }}>
              {monthLabels[wi]}
            </div>
            {week.map((cell) => {
              const inYear = cell.date.startsWith(String(year))
              const ratio = max > 0 && inYear ? cell.count / max : 0
              let bg = intensityColor(ratio, '--accent')
              if (
                inYear &&
                !sourceFilter &&
                cell.count > 0 &&
                cell.cursor > 0 &&
                cell.claude > 0
              ) {
                const cp = cell.cursor / cell.count
                bg = `linear-gradient(135deg, ${intensityColor(ratio * cp, '--accent')} 50%, ${intensityColor(ratio * (1 - cp), '--accent-secondary')} 50%)`
              } else if (sourceFilter === 'cursor') {
                bg = intensityColor(max > 0 && inYear ? cell.cursor / max : 0, '--accent')
              } else if (sourceFilter === 'claude-code') {
                bg = intensityColor(max > 0 && inYear ? cell.claude / max : 0, '--accent-secondary')
              }
              return (
                <div
                  key={`${wi}-${cell.date}`}
                  className="w-[12px] h-[12px] rounded-[2px] border border-transparent"
                  style={{
                    background: inYear ? bg : 'transparent',
                    borderColor:
                      inYear && cell.count > 0
                        ? 'color-mix(in srgb, var(--accent) 25%, transparent)'
                        : 'transparent',
                    opacity: inYear ? 1 : 0.15,
                  }}
                  title={
                    inYear
                      ? `${cell.date}: ${cell.count} (${cell.cursor} Cursor, ${cell.claude} Claude)`
                      : undefined
                  }
                />
              )
            })}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-3 mt-3 text-[10px]" style={{ color: 'var(--text-faint)' }}>
        <span>Less</span>
        {[0.15, 0.4, 0.7, 1].map((r) => (
          <div
            key={r}
            className="w-[12px] h-[12px] rounded-[2px]"
            style={{ background: intensityColor(r, '--accent') }}
          />
        ))}
        <span>More</span>
      </div>
    </div>
  )
}

function TimeHeatmap({
  cells = [],
  max = 0,
}: {
  cells?: DashboardInsights['time_heatmap']
  max?: number
}) {
  const grid = useMemo(() => {
    const m = new Map<string, (typeof cells)[0]>()
    for (const c of cells ?? []) m.set(`${c.dow}-${c.hour}`, c)
    return m
  }, [cells])

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        <div className="flex gap-[2px] mb-1 pl-8">
          {[0, 6, 12, 18, 23].map((h) => (
            <div
              key={h}
              className="text-[9px] flex-1 text-center"
              style={{ color: 'var(--text-faint)' }}
            >
              {h === 23 ? '23h' : `${h}h`}
            </div>
          ))}
        </div>
        {DOW_LABELS.map((label, dow) => (
          <div key={label} className="flex items-center gap-1 mb-[2px]">
            <div className="w-7 text-[9px] shrink-0" style={{ color: 'var(--text-faint)' }}>
              {label}
            </div>
            <div className="flex flex-1 gap-[2px]">
              {Array.from({ length: 24 }, (_, hour) => {
                const cell = grid.get(`${dow}-${hour}`) ?? { count: 0 }
                const ratio = max > 0 ? cell.count / max : 0
                return (
                  <div
                    key={hour}
                    className="flex-1 h-[16px] rounded-[2px] min-w-[8px] border border-transparent"
                    style={{
                      background: intensityColor(ratio, '--accent-warm'),
                      borderColor:
                        cell.count > 0
                          ? 'color-mix(in srgb, var(--accent-warm) 30%, transparent)'
                          : 'transparent',
                    }}
                    title={`${label} ${hour}:00 — ${cell.count} exchanges`}
                  />
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function WordCloud({ words }: { words: DashboardInsights['word_cloud'] }) {
  if (!words?.length) {
    return (
      <p className="text-sm text-center py-10" style={{ color: 'var(--text-faint)' }}>
        No prompt text for current filters.
      </p>
    )
  }
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-2 justify-center items-center py-4 px-2 min-h-[200px]">
      {words.map((w) => (
        <span
          key={w.text}
          className="font-medium leading-tight cursor-default"
          style={{
            fontSize: `${0.65 + w.weight * 1.1}rem`,
            color: `color-mix(in srgb, var(--accent) ${40 + w.weight * 60}%, var(--text-secondary))`,
          }}
          title={`${w.text}: ${w.count}`}
        >
          {w.text}
        </span>
      ))}
    </div>
  )
}

type NormalizedInsights = Required<
  Pick<
    DashboardInsights,
    | 'calendar_years'
    | 'calendar_year'
    | 'calendar'
    | 'calendar_max'
    | 'time_heatmap'
    | 'time_heatmap_max'
    | 'word_cloud'
  >
>

function normalizeInsights(raw: DashboardInsights): NormalizedInsights {
  const years = raw.calendar_years?.length
    ? raw.calendar_years
    : [raw.calendar_year ?? new Date().getFullYear()]
  return {
    calendar_years: years,
    calendar_year: raw.calendar_year ?? years[years.length - 1],
    calendar: raw.calendar ?? [],
    calendar_max: raw.calendar_max ?? 0,
    time_heatmap: raw.time_heatmap ?? [],
    time_heatmap_max: raw.time_heatmap_max ?? 0,
    word_cloud: raw.word_cloud ?? [],
  }
}

export function BehaviorInsights({
  data,
  sourceFilter,
  calendarYear,
  onCalendarYearChange,
}: {
  data: DashboardInsights | null
  sourceFilter: string
  calendarYear: number
  onCalendarYearChange: (year: number) => void
}) {
  if (!data) return null

  const insights = normalizeInsights(data)
  const years = insights.calendar_years

  return (
    <div className="space-y-4">
      <div className="glass p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="section-label">Activity calendar</div>
          <YearFilter years={years} selected={calendarYear} onChange={onCalendarYearChange} />
        </div>
        <CalendarHeatmap
          days={insights.calendar}
          max={insights.calendar_max}
          year={calendarYear}
          sourceFilter={sourceFilter}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass p-6">
          <div className="section-label mb-1">When you agent</div>
          <p className="text-[11px] mb-4" style={{ color: 'var(--text-faint)' }}>
            All-time · day × hour (global)
          </p>
          <TimeHeatmap cells={insights.time_heatmap} max={insights.time_heatmap_max} />
        </div>

        <div className="glass p-6">
          <div className="section-label mb-1">Prompt word cloud</div>
          <p className="text-[11px] mb-2" style={{ color: 'var(--text-faint)' }}>
            Top 25 words · follows dashboard filters above
          </p>
          <WordCloud words={insights.word_cloud} />
        </div>
      </div>
    </div>
  )
}
