import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../api/client'
import type {
  AnalyzeBounds,
  AnalyzeMode,
  AnalyzePreview,
  AnalyzeResult,
  AnalyzeSelection,
} from '../../types'

const EXPLAIN =
  'Uses your LLM to extract concepts from each message. Larger batches take longer and use more API credits.'

type Phase = 'confirm' | 'running' | 'done' | 'error'

interface Props {
  open: boolean
  onClose: () => void
  onComplete: (result: AnalyzeResult | null) => void
}

function parseYmd(iso: string): Date {
  return new Date(`${iso}T12:00:00Z`)
}

function daysBetween(min: string, max: string): number {
  const span = parseYmd(max).getTime() - parseYmd(min).getTime()
  return Math.max(0, Math.round(span / 86_400_000))
}

function addDaysYmd(iso: string, days: number): string {
  const d = parseYmd(iso)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

function formatYmdLabel(iso: string): string {
  return parseYmd(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function rangeDates(
  dateMin: string,
  dateMax: string,
  startDay: number,
  endDay: number,
): { since: string; until: string } {
  const totalDays = daysBetween(dateMin, dateMax)
  const since = addDaysYmd(dateMin, startDay)
  const until = endDay >= totalDays ? dateMax : addDaysYmd(dateMin, endDay)
  return { since, until }
}

export function RunAnalysisModal({ open, onClose, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>('confirm')
  const [mode, setMode] = useState<AnalyzeMode>('recent')
  const [bounds, setBounds] = useState<AnalyzeBounds | null>(null)
  const [boundsLoading, setBoundsLoading] = useState(false)
  const [limit, setLimit] = useState(50)
  const [rangeStartDay, setRangeStartDay] = useState(0)
  const [rangeEndDay, setRangeEndDay] = useState(0)
  const [preview, setPreview] = useState<AnalyzePreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [result, setResult] = useState<AnalyzeResult | null>(null)

  const dateMin = bounds?.date_min ?? null
  const dateMax = bounds?.date_max ?? null
  const totalDays = dateMin && dateMax ? daysBetween(dateMin, dateMax) : 0

  const selection: AnalyzeSelection = useMemo(() => {
    if (mode === 'recent') {
      return { mode: 'recent', limit }
    }
    if (dateMin && dateMax) {
      const { since, until } = rangeDates(dateMin, dateMax, rangeStartDay, rangeEndDay)
      return { mode: 'range', since, until }
    }
    return { mode: 'range' }
  }, [mode, limit, dateMin, dateMax, rangeStartDay, rangeEndDay])

  useEffect(() => {
    if (!open) return
    setPhase('confirm')
    setMode('recent')
    setBounds(null)
    setPreview(null)
    setProgress(0)
    setMessage('')
    setResult(null)
    setBoundsLoading(true)
    api
      .analyzeBounds()
      .then((b) => {
        setBounds(b)
        setLimit(b.recent_limit_default)
        const span = b.date_min && b.date_max ? daysBetween(b.date_min, b.date_max) : 0
        setRangeStartDay(0)
        setRangeEndDay(span)
      })
      .catch(() => setBounds(null))
      .finally(() => setBoundsLoading(false))
  }, [open])

  useEffect(() => {
    if (!open || phase !== 'confirm' || boundsLoading) return
    let cancelled = false
    setPreviewLoading(true)
    const timer = window.setTimeout(() => {
      api
        .analyzePreview(selection)
        .then((p) => {
          if (!cancelled) setPreview(p)
        })
        .catch(() => {
          if (!cancelled) setPreview(null)
        })
        .finally(() => {
          if (!cancelled) setPreviewLoading(false)
        })
    }, 200)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [open, phase, boundsLoading, selection])

  const handleStart = async () => {
    setPhase('running')
    setProgress(0)
    setMessage('Starting analysis…')
    try {
      const analyzeResult = await api.analyzeStream(selection, (evt) => {
        setProgress(evt.progress)
        setMessage(evt.message)
      })
      setResult(analyzeResult)
      setPhase('done')
      onComplete(analyzeResult)
    } catch (e) {
      setPhase('error')
      setMessage(
        e instanceof Error ? e.message : 'Analysis failed. Check LLM key in Settings.',
      )
      onComplete(null)
    }
  }

  const recentMin = bounds?.recent_limit_min ?? 1
  const recentMax = bounds?.recent_limit_max ?? 1
  const canStart =
    preview != null && preview.to_process > 0 && !previewLoading && !boundsLoading

  const rangeSince =
    dateMin && dateMax ? rangeDates(dateMin, dateMax, rangeStartDay, rangeEndDay).since : null
  const rangeUntil =
    dateMin && dateMax ? rangeDates(dateMin, dateMax, rangeStartDay, rangeEndDay).until : null

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4"
      style={{ background: 'rgba(15, 23, 42, 0.45)' }}
      onClick={phase === 'running' ? undefined : onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="run-analysis-title"
        className="glass w-full max-w-md rounded-2xl p-6 shadow-xl animate-fade-in-up flex flex-col overflow-hidden"
        style={{ color: 'var(--text-primary)', height: '28rem' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="run-analysis-title" className="font-display text-lg font-bold tracking-tight shrink-0">
          Run Analysis
        </h2>

        {phase === 'confirm' && (
          <>
            <p className="text-sm mt-3 leading-relaxed shrink-0" style={{ color: 'var(--text-muted)' }}>
              {EXPLAIN}
            </p>

            <div className="mt-4 flex gap-2 shrink-0">
              {(
                [
                  { id: 'recent' as const, label: 'Recent messages' },
                  { id: 'period' as const, label: 'Date range' },
                ] as const
              ).map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setMode(opt.id)}
                  className="flex-1 px-3 py-2 rounded-xl text-[12px] font-semibold cursor-pointer transition-all"
                  style={
                    mode === opt.id
                      ? { background: 'var(--accent)', color: '#fff' }
                      : {
                          background: 'var(--surface-raised)',
                          color: 'var(--text-muted)',
                        }
                  }
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <div className="mt-5 relative h-40 shrink-0">
              {boundsLoading && (
                <p
                  className="absolute inset-0 flex items-center text-sm"
                  style={{ color: 'var(--text-faint)' }}
                >
                  Loading options…
                </p>
              )}
              <div
                className="absolute inset-0"
                style={{
                  visibility: !boundsLoading && mode === 'recent' ? 'visible' : 'hidden',
                  pointerEvents: !boundsLoading && mode === 'recent' ? 'auto' : 'none',
                }}
              >
                <div
                  className="flex justify-between text-[12px] mb-2"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <span>How many recent messages</span>
                  <span className="font-bold tabular-nums" style={{ color: 'var(--accent)' }}>
                    {limit}
                  </span>
                </div>
                <input
                  type="range"
                  min={recentMin}
                  max={recentMax}
                  step={1}
                  value={Math.min(limit, recentMax)}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  disabled={recentMax <= 0 || bounds?.total_unanalyzed === 0}
                  className="w-full accent-[var(--accent)]"
                />
                <div
                  className="flex justify-between text-[10px] mt-1 tabular-nums"
                  style={{ color: 'var(--text-faint)' }}
                >
                  <span>{recentMin}</span>
                  <span>{recentMax}</span>
                </div>
              </div>
              <div
                className="absolute inset-0 space-y-3"
                style={{
                  visibility:
                    !boundsLoading && mode === 'period' && dateMin && dateMax
                      ? 'visible'
                      : 'hidden',
                  pointerEvents:
                    !boundsLoading && mode === 'period' && dateMin && dateMax ? 'auto' : 'none',
                }}
              >
                <div>
                  <div
                    className="flex justify-between text-[12px] mb-1"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    <span>From</span>
                    <span className="font-medium tabular-nums">
                      {rangeSince ? formatYmdLabel(rangeSince) : '—'}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={totalDays}
                    step={1}
                    value={rangeStartDay}
                    onChange={(e) => {
                      const v = Number(e.target.value)
                      setRangeStartDay(Math.min(v, rangeEndDay))
                    }}
                    className="w-full accent-[var(--accent)]"
                  />
                </div>
                <div>
                  <div
                    className="flex justify-between text-[12px] mb-1"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    <span>To</span>
                    <span className="font-medium tabular-nums">
                      {rangeUntil ? formatYmdLabel(rangeUntil) : '—'}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={totalDays}
                    step={1}
                    value={rangeEndDay}
                    onChange={(e) => {
                      const v = Number(e.target.value)
                      setRangeEndDay(Math.max(v, rangeStartDay))
                    }}
                    className="w-full accent-[var(--accent-secondary)]"
                  />
                </div>
              </div>
              {!boundsLoading && mode === 'period' && (!dateMin || !dateMax) && (
                <p
                  className="absolute inset-0 flex items-center text-sm"
                  style={{ color: 'var(--text-faint)' }}
                >
                  No unanalyzed messages with dates to filter.
                </p>
              )}
            </div>

            <div
              className="mt-4 px-3 py-2.5 rounded-xl text-[12px] h-16 shrink-0 overflow-hidden"
              style={{ background: 'var(--surface-raised)', color: 'var(--text-secondary)' }}
            >
              <p className="line-clamp-1 font-medium">
                {previewLoading || boundsLoading
                  ? '\u00a0'
                  : preview?.summary ?? '\u00a0'}
              </p>
              <p className="line-clamp-1 mt-1" style={{ color: 'var(--text-faint)' }}>
                {previewLoading || boundsLoading
                  ? 'Updating selection…'
                  : preview?.detail ??
                    (preview ? '' : 'Could not load preview. Is the backend running?')}
              </p>
            </div>

            <div className="flex gap-2.5 justify-end mt-auto pt-6 shrink-0">
              <button
                type="button"
                onClick={onClose}
                className="glass-subtle px-4 py-2 text-[13px] font-medium rounded-xl cursor-pointer"
                style={{ color: 'var(--text-secondary)' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleStart}
                disabled={!canStart}
                className="px-4 py-2 text-[13px] font-semibold rounded-xl cursor-pointer disabled:opacity-40"
                style={{
                  background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                  color: '#fff',
                }}
              >
                Start analysis
              </button>
            </div>
          </>
        )}

        {(phase === 'running' || phase === 'done' || phase === 'error') && (
          <>
            <p
              className="text-sm mt-3 line-clamp-3 shrink-0"
              style={{ color: 'var(--text-muted)' }}
              title={message}
            >
              {message}
            </p>
            {phase === 'running' && (
              <div className="mt-5 shrink-0">
                <div
                  className="h-2 rounded-full overflow-hidden"
                  style={{ background: 'var(--surface-raised)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-300 ease-out"
                    style={{
                      width: `${progress}%`,
                      background:
                        'linear-gradient(90deg, var(--accent), var(--accent-secondary))',
                    }}
                  />
                </div>
                <p className="text-xs mt-2 tabular-nums" style={{ color: 'var(--text-muted)' }}>
                  {message} · {progress}%
                </p>
              </div>
            )}
            {phase === 'done' && result && (
              <p className="text-sm mt-4 font-medium shrink-0" style={{ color: 'var(--accent)' }}>
                {result.processed} analyzed
                {result.errors > 0 ? `, ${result.errors} failed` : ''}. {result.remaining} still
                unanalyzed.
              </p>
            )}
            {phase !== 'running' && (
              <div className="flex justify-end mt-auto pt-6 shrink-0">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-[13px] font-semibold rounded-xl cursor-pointer"
                  style={{
                    background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                    color: '#fff',
                  }}
                >
                  Close
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>,
    document.body,
  )
}
