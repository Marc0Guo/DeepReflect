import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { MarkdownRenderer } from '../components/Study/MarkdownRenderer'
import { QuizCard } from '../components/Study/QuizCard'
import type { Flashcard, QuizQuestion } from '../types'

const TABS = [
  { key: 'flashcards' as const, label: 'Flashcards', icon: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="2" y="6" width="16" height="14" rx="2" /><path d="M6 2h12a2 2 0 0 1 2 2v12" /></svg>
  )},
  { key: 'guide' as const, label: 'Study Guide', icon: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>
  )},
  { key: 'quiz' as const, label: 'Quiz', icon: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
  )},
]

export function StudyPage() {
  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [guide, setGuide] = useState('')
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([])
  const [tab, setTab] = useState<'flashcards' | 'guide' | 'quiz'>('flashcards')
  const [guideLoading, setGuideLoading] = useState(false)
  const [quizLoading, setQuizLoading] = useState(false)
  const [flipped, setFlipped] = useState<Set<number>>(new Set())
  const [generating, setGenerating] = useState(false)
  const [guideLoaded, setGuideLoaded] = useState(false)
  const [quizLoaded, setQuizLoaded] = useState(false)

  useEffect(() => { api.flashcards().then(setFlashcards).catch(() => {}) }, [])

  async function loadGuide() {
    if (guideLoaded) return
    setGuideLoading(true)
    try { const r = await api.studyGuide('this week'); setGuide(r.guide); setGuideLoaded(true) }
    catch { setGuide('**Error loading study guide.** Make sure your LLM API key is configured.'); setGuideLoaded(true) }
    setGuideLoading(false)
  }

  async function loadQuiz() {
    setQuizLoading(true)
    try { const r = await api.quiz(); setQuizQuestions(r.questions || []); setQuizLoaded(true) }
    catch { setQuizQuestions([]); setQuizLoaded(true) }
    setQuizLoading(false)
  }

  async function generateCards() {
    setGenerating(true)
    try { await api.generateFlashcards(15); setFlashcards(await api.flashcards()) } catch {}
    setGenerating(false)
  }

  function toggleFlip(id: number) {
    setFlipped((prev) => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })
  }

  return (
    <div className="p-8 lg:p-10 max-w-5xl mx-auto space-y-8">
      <div className="animate-fade-in-up">
        <h1 className="font-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>Study Materials</h1>
        <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>Generated from your AI conversation history.</p>
      </div>

      <div className="flex gap-1 p-1 rounded-[14px] w-fit animate-fade-in-up stagger-1" style={{ background: 'var(--surface-raised)', border: '1px solid var(--glass-border)' }}>
        {TABS.map((t) => (
          <button key={t.key}
            onClick={() => { setTab(t.key); if (t.key === 'guide' && !guideLoaded) loadGuide(); if (t.key === 'quiz' && !quizLoaded) loadQuiz() }}
            className="flex items-center gap-2 px-4 py-2 text-[13px] font-medium rounded-[10px] transition-all duration-200 cursor-pointer"
            style={{
              color: tab === t.key ? 'var(--accent)' : 'var(--text-muted)',
              background: tab === t.key ? 'color-mix(in srgb, var(--accent) 12%, transparent)' : 'transparent',
              boxShadow: tab === t.key ? 'inset 0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent)' : 'none',
            }}>
            {t.icon}
            {t.key === 'flashcards' ? `Flashcards (${flashcards.length})` : t.label}
          </button>
        ))}
      </div>

      {tab === 'flashcards' && (
        <div className="space-y-5 animate-fade-in">
          <div className="flex justify-between items-center">
            <span className="text-xs" style={{ color: 'var(--text-faint)' }}>{flashcards.length} cards · click to flip</span>
            <button onClick={generateCards} disabled={generating}
              className="px-4 py-2 text-[13px] font-semibold rounded-[14px] transition-all disabled:opacity-40 flex items-center gap-2 cursor-pointer"
              style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))', color: 'white', boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 25%, transparent)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>
              {generating ? 'Generating...' : 'Generate from Conversations'}
            </button>
          </div>

          {flashcards.length === 0 && (
            <div className="glass py-16 text-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3" style={{ color: 'var(--text-faint)' }}><rect x="2" y="6" width="16" height="14" rx="2" /><path d="M6 2h12a2 2 0 0 1 2 2v12" /></svg>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No flashcards yet.</p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-faint)' }}>Click "Generate from Conversations" to create some.</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {flashcards.map((c, i) => (
              <div key={c.id} onClick={() => toggleFlip(c.id)}
                className="cursor-pointer glass glass-hover p-6 min-h-[140px] flex flex-col justify-between relative overflow-hidden animate-fade-in-up group"
                style={{ animationDelay: `${i * 40}ms` }}>
                <div className="absolute top-0 left-0 w-full h-[2px] opacity-50"
                  style={{ background: flipped.has(c.id) ? 'linear-gradient(90deg, var(--accent-secondary), transparent)' : 'linear-gradient(90deg, var(--accent), transparent)' }} />
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: flipped.has(c.id) ? 'var(--accent-secondary)' : 'var(--accent)' }} />
                  <span className="section-label">{flipped.has(c.id) ? 'Answer' : 'Question'}</span>
                </div>
                <p className="text-sm leading-relaxed flex-1" style={{ color: 'var(--text-secondary)' }}>{flipped.has(c.id) ? c.back : c.front}</p>
                <div className="text-[10px] mt-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text-faint)' }}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>
                  tap to {flipped.has(c.id) ? 'see question' : 'reveal answer'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'guide' && (
        <div className="animate-fade-in">
          {guideLoading ? (
            <div className="glass p-10 flex flex-col items-center gap-4">
              <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Generating your personalized study guide...</span>
              <span className="text-xs" style={{ color: 'var(--text-faint)' }}>This may take a few seconds</span>
            </div>
          ) : guide ? (
            <div className="glass p-8 lg:p-10"><MarkdownRenderer content={guide} /></div>
          ) : (
            <div className="glass p-10 text-center"><p className="text-sm" style={{ color: 'var(--text-muted)' }}>Click to load your study guide.</p></div>
          )}
        </div>
      )}

      {tab === 'quiz' && (
        <div className="max-w-2xl mx-auto animate-fade-in">
          {quizLoading ? (
            <div className="glass p-10 flex flex-col items-center gap-4">
              <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent-secondary) 30%, transparent)', borderTopColor: 'var(--accent-secondary)' }} />
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Generating quiz questions...</span>
              <span className="text-xs" style={{ color: 'var(--text-faint)' }}>Creating 5 questions from your top concepts</span>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: 'var(--text-faint)' }}>{quizQuestions.length} questions · select or type your answers</span>
                {quizLoaded && (
                  <button onClick={() => { setQuizLoaded(false); loadQuiz() }}
                    className="glass-subtle px-3 py-1.5 text-xs font-medium rounded-[10px] transition-colors flex items-center gap-1.5 cursor-pointer"
                    style={{ color: 'var(--text-muted)' }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>
                    New Quiz
                  </button>
                )}
              </div>
              <QuizCard questions={quizQuestions} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
