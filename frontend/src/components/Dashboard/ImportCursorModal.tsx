import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../api/client'
import type { CursorImportProgress, IngestResult } from '../../types'

const SLOW_REASON =
  'This reads Cursor’s local SQLite database and every agent transcript on disk, which can take a minute on large histories.'

type Phase = 'confirm' | 'importing' | 'done' | 'error'

interface Props {
  open: boolean
  onClose: () => void
  onComplete: (result: IngestResult | null) => void
}

export function ImportCursorModal({ open, onClose, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>('confirm')
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [result, setResult] = useState<IngestResult | null>(null)

  useEffect(() => {
    if (!open) return
    setPhase('confirm')
    setProgress(0)
    setMessage('')
    setResult(null)
  }, [open])

  const handleStart = async () => {
    setPhase('importing')
    setProgress(0)
    setMessage('Starting import…')
    try {
      const ingestResult = await api.ingestCursorStream((evt: CursorImportProgress) => {
        setProgress(evt.progress)
        setMessage(evt.message)
      })
      setResult(ingestResult)
      setPhase('done')
      onComplete(ingestResult)
    } catch {
      setPhase('error')
      setMessage('Import failed. Is the backend running on port 7733?')
      onComplete(null)
    }
  }

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4"
      style={{ background: 'rgba(15, 23, 42, 0.45)' }}
      onClick={phase === 'importing' ? undefined : onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-cursor-title"
        className="glass w-full max-w-md rounded-2xl p-6 shadow-xl animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
        style={{ color: 'var(--text-primary)' }}
      >
        <h2
          id="import-cursor-title"
          className="font-display text-lg font-bold tracking-tight"
        >
          Import Cursor
        </h2>

        {phase === 'confirm' && (
          <>
            <p className="text-sm mt-3 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              {SLOW_REASON}
            </p>
            <div className="flex gap-2.5 justify-end mt-6">
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
                className="px-4 py-2 text-[13px] font-semibold rounded-xl cursor-pointer"
                style={{
                  background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                  color: '#fff',
                }}
              >
                Start import
              </button>
            </div>
          </>
        )}

        {(phase === 'importing' || phase === 'done' || phase === 'error') && (
          <>
            <p className="text-sm mt-3" style={{ color: 'var(--text-muted)' }}>
              {phase === 'importing' ? SLOW_REASON : message}
            </p>
            {phase === 'importing' && (
              <div className="mt-5">
                <div
                  className="h-2 rounded-full overflow-hidden"
                  style={{ background: 'var(--surface-elevated)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-300 ease-out"
                    style={{
                      width: `${progress}%`,
                      background: 'linear-gradient(90deg, var(--accent), var(--accent-secondary))',
                    }}
                  />
                </div>
                <p className="text-xs mt-2 tabular-nums" style={{ color: 'var(--text-muted)' }}>
                  {message} · {progress}%
                </p>
              </div>
            )}
            {phase === 'done' && result && (
              <p className="text-sm mt-4 font-medium" style={{ color: 'var(--accent)' }}>
                Imported {result.imported} turns ({result.new} new).
              </p>
            )}
            {phase !== 'importing' && (
              <div className="flex justify-end mt-6">
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
