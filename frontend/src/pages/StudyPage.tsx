import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { MarkdownRenderer } from '../components/Study/MarkdownRenderer'
import { QuizCard } from '../components/Study/QuizCard'
import type { Flashcard, HistoryItem, QuizQuestion } from '../types'

type Tab = 'flashcards' | 'guide' | 'quiz'

const TABS: { key: Tab; label: string }[] = [
  { key: 'flashcards', label: 'Flashcards' },
  { key: 'guide',      label: 'Study Guide' },
  { key: 'quiz',       label: 'Quiz' },
]

// ── Liquid pill tab bar ───────────────────────────────────────────────────────

function TabBar({
  tabs,
  active,
  onChange,
  badge,
}: {
  tabs: { key: Tab; label: string }[]
  active: Tab
  onChange: (t: Tab) => void
  badge?: Partial<Record<Tab, string | number>>
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const btnRefs = useRef<Partial<Record<Tab, HTMLButtonElement | null>>>({})
  const [pill, setPill] = useState({ left: 0, width: 0, ready: false })

  useEffect(() => {
    const el = btnRefs.current[active]
    const container = containerRef.current
    if (el && container) {
      setPill({
        left: el.offsetLeft,
        width: el.offsetWidth,
        ready: true,
      })
    }
  }, [active])

  return (
    <div
      ref={containerRef}
      className="relative flex gap-0 p-1 w-fit"
      style={{
        borderRadius: 16,
        background: 'var(--chrome-rail)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
      }}
    >
      {/* Sliding pill */}
      {pill.ready && (
        <div
          aria-hidden
          className="absolute top-1 bottom-1 pointer-events-none"
          style={{
            left: pill.left,
            width: pill.width,
            borderRadius: 12,
            background: 'var(--chrome-pill)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            boxShadow: 'var(--chrome-pill-highlight)',
            transition: 'left 0.38s cubic-bezier(0.34,1.56,0.64,1), width 0.28s cubic-bezier(0.34,1.56,0.64,1)',
          }}
        />
      )}

      {tabs.map((t) => {
        const isActive = t.key === active
        return (
          <button
            key={t.key}
            ref={(el) => { btnRefs.current[t.key] = el }}
            onClick={() => onChange(t.key)}
            className="relative flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium rounded-[12px] cursor-pointer transition-colors duration-200"
            style={{
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              background: 'transparent',
              zIndex: 1,
            }}
          >
            {t.label}
            {badge?.[t.key] !== undefined && (
              <span
                className="text-[10px] font-semibold tabular-nums px-1.5 py-0.5 rounded-full"
                style={{
                  background: isActive
                    ? 'color-mix(in srgb, var(--accent) 18%, transparent)'
                    : 'var(--chrome-rail)',
                  color: isActive ? 'var(--accent)' : 'var(--text-faint)',
                  transition: 'background 0.25s, color 0.25s',
                }}
              >
                {badge[t.key]}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

// ── History list ──────────────────────────────────────────────────────────────

function HistoryList({
  items,
  onSelect,
  selectedId,
}: {
  items: HistoryItem[]
  onSelect: (i: HistoryItem) => void
  selectedId: number | null
}) {
  if (!items.length)
    return <div className="text-center py-8 text-xs" style={{ color: 'var(--text-faint)' }}>No history yet.</div>

  return (
    <div className="space-y-1.5">
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => onSelect(item)}
          className="w-full text-left px-4 py-3 rounded-[12px] transition-all duration-200 cursor-pointer"
          style={{
            background: selectedId === item.id ? 'var(--chrome-pill)' : 'transparent',
            backdropFilter: selectedId === item.id ? 'blur(8px)' : 'none',
            WebkitBackdropFilter: selectedId === item.id ? 'blur(8px)' : 'none',
            boxShadow: selectedId === item.id ? 'var(--chrome-pill-highlight)' : 'none',
          }}
        >
          <div className="text-[12px] font-semibold truncate" style={{ color: selectedId === item.id ? 'var(--accent)' : 'var(--text-secondary)' }}>
            {item.title}
          </div>
          <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-faint)' }}>
            {new Date(item.created_at).toLocaleString()}
          </div>
        </button>
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function StudyPage() {
  const [tab, setTab] = useState<Tab>('flashcards')
  const [displayedTab, setDisplayedTab] = useState<Tab>('flashcards')
  const [contentKey, setContentKey] = useState(0) // increment to re-trigger enter anim

  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [guide, setGuide] = useState('')
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([])

  const [guideLoading, setGuideLoading] = useState(false)
  const [quizLoading, setQuizLoading] = useState(false)
  const [flipped, setFlipped] = useState<Set<number>>(new Set())
  const [generating, setGenerating] = useState(false)

  const [quizHistory, setQuizHistory] = useState<HistoryItem[]>([])
  const [guideHistory, setGuideHistory] = useState<HistoryItem[]>([])
  const [selectedQuizId, setSelectedQuizId] = useState<number | null>(null)
  const [selectedGuideId, setSelectedGuideId] = useState<number | null>(null)
  const [guideView, setGuideView] = useState<'new' | 'history'>('new')
  const [quizView, setQuizView] = useState<'new' | 'history'>('new')

  useEffect(() => { api.flashcards().then(setFlashcards).catch(() => {}) }, [])

  // Liquid tab switch: exit anim → swap content → enter anim
  function switchTab(newTab: Tab) {
    if (newTab === tab) return
    setTab(newTab)
    // Small delay lets the exit frame paint before content swaps
    requestAnimationFrame(() => {
      setTimeout(() => {
        setDisplayedTab(newTab)
        setContentKey((k) => k + 1)
      }, 90)
    })
    if (newTab === 'guide') loadGuideHistory()
    if (newTab === 'quiz')  loadQuizHistory()
  }

  function loadQuizHistory() {
    api.quizHistory().then(setQuizHistory).catch(() => {})
  }
  function loadGuideHistory() {
    api.guideHistory().then(setGuideHistory).catch(() => {})
  }

  async function generateGuide() {
    setGuideLoading(true); setGuideView('new')
    try {
      const r = await api.studyGuide('this week')
      setGuide(r.guide)
      loadGuideHistory()
    } catch { setGuide('**Error.** Make sure your LLM API key is configured in Settings.') }
    setGuideLoading(false)
  }

  async function generateQuiz() {
    setQuizLoading(true); setQuizView('new')
    try {
      const r = await api.quiz()
      setQuizQuestions(r.questions || [])
      loadQuizHistory()
    } catch { setQuizQuestions([]) }
    setQuizLoading(false)
  }

  async function generateCards() {
    setGenerating(true)
    try { await api.generateFlashcards(15); setFlashcards(await api.flashcards()) } catch {}
    setGenerating(false)
  }

  function toggleFlip(id: number) {
    setFlipped((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const historyQuizSelected  = quizHistory.find((h) => h.id === selectedQuizId)
  const historyGuideSelected = guideHistory.find((h) => h.id === selectedGuideId)

  // Whether displayed tab matches active tab (during transition it differs)
  const isTransitioning = displayedTab !== tab

  return (
    <div className="p-8 lg:p-10 max-w-5xl mx-auto space-y-8">
      <div className="animate-fade-in-up">
        <h1 className="font-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          Study Materials
        </h1>
        <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>
          Generated from your AI conversation history.
        </p>
      </div>

      {/* Tab bar */}
      <div className="animate-fade-in-up stagger-1">
        <TabBar
          tabs={TABS}
          active={tab}
          onChange={switchTab}
          badge={{ flashcards: flashcards.length }}
        />
      </div>

      {/* Content — key + class drive enter/exit */}
      <div
        key={contentKey}
        className={isTransitioning ? 'tab-exit' : 'tab-enter'}
      >

        {/* ── FLASHCARDS ─────────────────────────────────────────────── */}
        {displayedTab === 'flashcards' && (
          <div className="space-y-5">
            <div className="flex justify-between items-center">
              <span className="text-xs" style={{ color: 'var(--text-faint)' }}>
                {flashcards.length} cards · click to flip
              </span>
              <button
                onClick={generateCards}
                disabled={generating}
                className="px-4 py-2 text-[13px] font-semibold rounded-[14px] transition-all disabled:opacity-40 flex items-center gap-2 cursor-pointer"
                style={{
                  background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                  color: 'white',
                  boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 25%, transparent)',
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                {generating ? 'Generating…' : 'Generate from Conversations'}
              </button>
            </div>

            {flashcards.length === 0 && (
              <div className="glass py-16 text-center">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3" style={{ color: 'var(--text-faint)' }}><rect x="2" y="6" width="16" height="14" rx="2"/><path d="M6 2h12a2 2 0 0 1 2 2v12"/></svg>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No flashcards yet.</p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-faint)' }}>Click "Generate from Conversations" to create some.</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {flashcards.map((c, i) => (
                <div
                  key={c.id}
                  onClick={() => toggleFlip(c.id)}
                  className="cursor-pointer glass glass-hover p-6 min-h-[140px] flex flex-col justify-between relative overflow-hidden animate-fade-in-up group"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <div className="absolute top-0 left-0 w-full h-[2px] opacity-50"
                    style={{ background: flipped.has(c.id) ? 'linear-gradient(90deg, var(--accent-secondary), transparent)' : 'linear-gradient(90deg, var(--accent), transparent)' }} />
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: flipped.has(c.id) ? 'var(--accent-secondary)' : 'var(--accent)' }} />
                    <span className="section-label">{flipped.has(c.id) ? 'Answer' : 'Question'}</span>
                  </div>
                  <p className="text-sm leading-relaxed flex-1" style={{ color: 'var(--text-secondary)' }}>
                    {flipped.has(c.id) ? c.back : c.front}
                  </p>
                  <div className="text-[10px] mt-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text-faint)' }}>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                    tap to {flipped.has(c.id) ? 'see question' : 'reveal answer'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── STUDY GUIDE ────────────────────────────────────────────── */}
        {displayedTab === 'guide' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <TabBar
                tabs={[{ key: 'new' as unknown as Tab, label: 'Current' }, { key: 'history' as unknown as Tab, label: `History (${guideHistory.length})` }]}
                active={guideView as unknown as Tab}
                onChange={(v) => setGuideView(v as unknown as 'new' | 'history')}
              />
              <button
                onClick={generateGuide}
                disabled={guideLoading}
                className="ml-auto px-4 py-2 text-[12px] font-semibold rounded-[12px] transition-all disabled:opacity-40 flex items-center gap-1.5 cursor-pointer"
                style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white' }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                {guideLoading ? 'Generating…' : 'Generate New'}
              </button>
            </div>

            {guideView === 'history' ? (
              <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-4">
                <div className="glass p-3">
                  <div className="section-label px-2 mb-2">Past Guides</div>
                  <HistoryList items={guideHistory} selectedId={selectedGuideId} onSelect={(item) => setSelectedGuideId(item.id)} />
                </div>
                <div className="glass p-6 lg:p-8">
                  {historyGuideSelected
                    ? <MarkdownRenderer content={historyGuideSelected.content ?? ''} />
                    : <p className="text-sm text-center py-8" style={{ color: 'var(--text-faint)' }}>Select a guide from the list</p>
                  }
                </div>
              </div>
            ) : guideLoading ? (
              <div className="glass p-10 flex flex-col items-center gap-4">
                <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Generating your personalized study guide…</span>
              </div>
            ) : guide ? (
              <div className="glass p-8 lg:p-10"><MarkdownRenderer content={guide} /></div>
            ) : (
              <div className="glass p-10 text-center">
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Click "Generate New" to create a study guide.</p>
              </div>
            )}
          </div>
        )}

        {/* ── QUIZ ───────────────────────────────────────────────────── */}
        {displayedTab === 'quiz' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <TabBar
                tabs={[{ key: 'new' as unknown as Tab, label: 'Current' }, { key: 'history' as unknown as Tab, label: `History (${quizHistory.length})` }]}
                active={quizView as unknown as Tab}
                onChange={(v) => setQuizView(v as unknown as 'new' | 'history')}
              />
              <button
                onClick={generateQuiz}
                disabled={quizLoading}
                className="ml-auto px-4 py-2 text-[12px] font-semibold rounded-[12px] transition-all disabled:opacity-40 flex items-center gap-1.5 cursor-pointer"
                style={{ background: 'linear-gradient(135deg, var(--accent-secondary), var(--accent))', color: 'white' }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                {quizLoading ? 'Generating…' : 'Generate New Quiz'}
              </button>
            </div>

            {quizView === 'history' ? (
              <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-4">
                <div className="glass p-3">
                  <div className="section-label px-2 mb-2">Past Quizzes</div>
                  <HistoryList items={quizHistory} selectedId={selectedQuizId} onSelect={(item) => setSelectedQuizId(item.id)} />
                </div>
                <div className="max-w-2xl">
                  {historyQuizSelected
                    ? <QuizCard key={selectedQuizId} questions={historyQuizSelected.questions ?? []} />
                    : <div className="glass p-10 text-center text-sm" style={{ color: 'var(--text-faint)' }}>Select a quiz from the list</div>
                  }
                </div>
              </div>
            ) : quizLoading ? (
              <div className="glass p-10 flex flex-col items-center gap-4 max-w-2xl mx-auto">
                <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent-secondary) 30%, transparent)', borderTopColor: 'var(--accent-secondary)' }} />
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Generating quiz questions…</span>
              </div>
            ) : (
              <div className="max-w-2xl mx-auto">
                {quizQuestions.length > 0
                  ? <QuizCard questions={quizQuestions} />
                  : (
                    <div className="glass p-10 text-center">
                      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Click "Generate New Quiz" to start.</p>
                      <p className="text-xs mt-1" style={{ color: 'var(--text-faint)' }}>Analyze conversations first to build concept history.</p>
                    </div>
                  )
                }
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
