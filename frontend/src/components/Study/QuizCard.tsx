import { useState } from 'react'
import type { QuizQuestion } from '../../types'

interface Props { questions: QuizQuestion[] }
type AnswerState = 'unanswered' | 'correct' | 'wrong'

export function QuizCard({ questions }: Props) {
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [shortAnswer, setShortAnswer] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered')
  const [score, setScore] = useState(0)
  const [swiping, setSwiping] = useState<'left' | 'right' | null>(null)
  const [finished, setFinished] = useState(false)

  if (!questions.length) {
    return (
      <div className="glass py-16 text-center">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3" style={{ color: 'var(--text-faint)' }}>
          <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No quiz questions generated.</p>
        <p className="text-xs mt-1" style={{ color: 'var(--text-faint)' }}>Make sure you have analyzed concepts first.</p>
      </div>
    )
  }

  if (finished) {
    const pct = Math.round((score / questions.length) * 100)
    return (
      <div className="glass p-10 text-center animate-fade-in-up">
        <div className="text-5xl mb-4">{pct >= 80 ? '🎉' : pct >= 50 ? '💪' : '📚'}</div>
        <div className="font-display text-5xl font-extrabold mb-2" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          {score}/{questions.length}
        </div>
        <div className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>{pct}% correct</div>
        <div className="text-xs mb-6" style={{ color: 'var(--text-muted)' }}>
          {pct >= 80 ? 'Excellent work! You really know your stuff.' : pct >= 50 ? 'Good effort — keep reviewing the ones you missed.' : "Keep studying — you'll get there!"}
        </div>
        <button onClick={() => { setCurrent(0); setSelected(null); setShortAnswer(''); setRevealed(false); setAnswerState('unanswered'); setScore(0); setFinished(false) }}
          className="px-5 py-2.5 text-[13px] font-semibold rounded-[14px] transition-all cursor-pointer hover:scale-[1.02]"
          style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white', boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 30%, transparent)' }}>
          Retry Quiz
        </button>
      </div>
    )
  }

  const q = questions[current]
  const isMC = q.type === 'multiple_choice' && q.choices

  function handleSubmit() {
    if (revealed) return
    if (isMC && selected === null) return
    if (!isMC && !shortAnswer.trim()) return
    setRevealed(true)
    if (isMC && q.choices) {
      const isCorrect = q.choices[selected!]?.is_correct
      setAnswerState(isCorrect ? 'correct' : 'wrong')
      if (isCorrect) setScore((s) => s + 1)
    } else { setAnswerState('correct'); setScore((s) => s + 1) }
  }

  function handleNext() {
    setSwiping(answerState === 'correct' ? 'right' : 'left')
    setTimeout(() => {
      setSwiping(null)
      if (current + 1 >= questions.length) { setFinished(true) }
      else { setCurrent((c) => c + 1); setSelected(null); setShortAnswer(''); setRevealed(false); setAnswerState('unanswered') }
    }, 300)
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface-raised)' }}>
          <div className="h-full rounded-full transition-all duration-500 ease-out" style={{ width: `${((current + (revealed ? 1 : 0)) / questions.length) * 100}%`, background: 'linear-gradient(90deg, var(--accent), var(--accent-secondary))' }} />
        </div>
        <span className="text-xs tabular-nums font-medium" style={{ color: 'var(--text-faint)' }}>{current + 1}/{questions.length}</span>
      </div>

      <div className="relative" style={{ minHeight: 380 }}>
        {current + 1 < questions.length && <div className="absolute inset-x-3 top-3 h-full glass opacity-40 -z-10" />}
        {current + 2 < questions.length && <div className="absolute inset-x-6 top-6 h-full glass opacity-20 -z-20" />}

        <div className={`glass p-8 relative overflow-hidden transition-all duration-300 ${swiping === 'right' ? 'quiz-swipe-right' : swiping === 'left' ? 'quiz-swipe-left' : ''} ${answerState === 'wrong' && revealed ? 'quiz-shake' : ''}`}>
          <div className="absolute top-0 left-0 w-full h-[3px]" style={{
            background: revealed
              ? answerState === 'correct' ? 'linear-gradient(90deg, var(--accent-green), var(--accent))' : 'linear-gradient(90deg, var(--accent-pink), var(--accent-secondary))'
              : 'linear-gradient(90deg, var(--accent-secondary), var(--accent))'
          }} />

          <div className="flex items-center justify-between mb-5">
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-lg" style={{
              background: `color-mix(in srgb, var(${isMC ? '--accent-secondary' : '--accent'}) 12%, transparent)`,
              color: `var(${isMC ? '--accent-secondary' : '--accent'})`
            }}>{isMC ? 'Multiple Choice' : 'Short Answer'}</span>
            <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>Q{current + 1}</span>
          </div>

          <h3 className="font-display text-lg font-bold leading-snug mb-6" style={{ color: 'var(--text-primary)' }}>{q.question}</h3>

          {isMC && q.choices && (
            <div className="space-y-2.5">
              {q.choices.map((choice, idx) => {
                const isSelected = selected === idx
                const letter = ['A', 'B', 'C', 'D'][idx]
                let borderCol = 'var(--glass-border)'
                let bgCol = 'var(--surface-raised)'
                let textCol = 'var(--text-secondary)'
                let badgeBg = 'var(--surface-raised)'
                let badgeCol = 'var(--text-faint)'

                if (isSelected && !revealed) {
                  borderCol = 'color-mix(in srgb, var(--accent-secondary) 50%, transparent)'; bgCol = 'color-mix(in srgb, var(--accent-secondary) 8%, transparent)'
                  textCol = 'var(--text-primary)'; badgeBg = 'var(--accent-secondary)'; badgeCol = 'white'
                }
                if (revealed && choice.is_correct) {
                  borderCol = 'color-mix(in srgb, var(--accent-green) 50%, transparent)'; bgCol = 'color-mix(in srgb, var(--accent-green) 8%, transparent)'
                  textCol = 'var(--accent-green)'; badgeBg = 'var(--accent-green)'; badgeCol = 'white'
                }
                if (revealed && isSelected && !choice.is_correct) {
                  borderCol = 'color-mix(in srgb, var(--accent-pink) 50%, transparent)'; bgCol = 'color-mix(in srgb, var(--accent-pink) 8%, transparent)'
                  textCol = 'var(--accent-pink)'; badgeBg = 'var(--accent-pink)'; badgeCol = 'white'
                }

                return (
                  <button key={idx} onClick={() => { if (!revealed) setSelected(idx) }} disabled={revealed}
                    className={`w-full text-left flex items-start gap-3 p-4 rounded-[14px] transition-all duration-200 ${!revealed ? 'cursor-pointer' : ''}`}
                    style={{ border: `1px solid ${borderCol}`, background: bgCol }}>
                    <span className="text-xs font-bold shrink-0 w-6 h-6 rounded-lg flex items-center justify-center" style={{ background: badgeBg, color: badgeCol }}>
                      {revealed && choice.is_correct ? '✓' : revealed && isSelected ? '✗' : letter}
                    </span>
                    <div className="flex-1 min-w-0">
                      <span className="text-[13px] leading-relaxed" style={{ color: textCol }}>{choice.text}</span>
                      {revealed && (isSelected || choice.is_correct) && (
                        <p className="text-xs mt-1.5 leading-relaxed animate-fade-in" style={{ color: 'var(--text-muted)' }}>{choice.explanation}</p>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          )}

          {!isMC && (
            <div className="space-y-4">
              <textarea value={shortAnswer} onChange={(e) => setShortAnswer(e.target.value)} disabled={revealed} placeholder="Type your answer..."
                className="w-full h-24 rounded-[14px] p-4 text-sm resize-none focus:outline-none transition-colors"
                style={{ background: 'var(--surface-raised)', border: '1px solid var(--glass-border)', color: 'var(--text-secondary)' }} />
              {revealed && (
                <div className="glass-subtle p-4 animate-fade-in-up" style={{ borderLeft: '2px solid var(--accent)' }}>
                  <div className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--accent)' }}>Answer</div>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{q.answer}</p>
                  {q.explanation && (<><div className="text-[10px] font-semibold uppercase tracking-wider mt-3 mb-1" style={{ color: 'var(--text-faint)' }}>Explanation</div><p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{q.explanation}</p></>)}
                </div>
              )}
            </div>
          )}

          <div className="mt-6 flex items-center justify-between">
            {!revealed ? (
              <>
                <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>{isMC ? 'Select an answer' : 'Type your answer'}</span>
                <button onClick={handleSubmit} disabled={isMC ? selected === null : !shortAnswer.trim()}
                  className="px-5 py-2.5 text-[13px] font-semibold rounded-[14px] transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                  style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white', boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 25%, transparent)' }}>Submit</button>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: answerState === 'correct' ? 'var(--accent-green)' : 'var(--accent-pink)' }}>
                  {answerState === 'correct' ? (
                    <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>Correct!</>
                  ) : (
                    <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>Not quite</>
                  )}
                </div>
                <button onClick={handleNext} className="glass-subtle px-5 py-2.5 text-[13px] font-semibold rounded-[14px] transition-all flex items-center gap-2 cursor-pointer" style={{ color: 'var(--text-secondary)' }}>
                  {current + 1 >= questions.length ? 'See Results' : 'Next'}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="9 18 15 12 9 6" /></svg>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
