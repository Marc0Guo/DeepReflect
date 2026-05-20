const BASE = '/api'

function appendFilterParams(p: URLSearchParams, filters?: import('../types').DashboardFilters) {
  if (!filters) return
  if (filters.period !== 'all') p.set('period', filters.period)
  if (filters.source) p.set('source', filters.source)
  if (filters.concept.trim()) p.set('concept', filters.concept.trim())
  if (filters.status !== 'all') p.set('status', filters.status)
}

function buildFilterQuery(filters?: import('../types').DashboardFilters): string {
  const p = new URLSearchParams()
  appendFilterParams(p, filters)
  const qs = p.toString()
  return qs ? `?${qs}` : ''
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  stats: (filters?: import('../types').DashboardFilters) =>
    get<import('../types').Stats>(`/summary/stats${buildFilterQuery(filters)}`),
  graph: () => get<import('../types').GraphData>('/graph'),
  concepts: (minAsk = 1, filters?: import('../types').DashboardFilters) => {
    const p = new URLSearchParams({ min_ask_count: String(minAsk) })
    appendFilterParams(p, filters)
    return get<import('../types').Concept[]>(`/graph/concepts?${p}`)
  },
  conceptTurns: (id: number, limit = 20) =>
    get<import('../types').ConversationTurn[]>(`/graph/concept/${id}/turns?limit=${limit}`),
  flashcards: () => get<import('../types').Flashcard[]>('/study/flashcards'),
  generateFlashcards: (limit = 10) => post('/study/flashcards/generate', { limit }),
  studyGuide: (period = 'this week') => get<{ guide: string }>(`/study/guide?period=${period}`),
  quiz: () => get<{ questions: import('../types').QuizQuestion[] }>('/study/quiz'),
  analyze: (limit = 50) => post<{ processed: number; errors: number }>(`/analyze?limit=${limit}`),
  ingestAll: () => post<import('../types').IngestResult>('/ingest/claude-code/all'),
  listProjects: () => get<{ projects: string[] }>('/ingest/projects'),
  ingestCursor: () => post<import('../types').IngestResult>('/ingest/cursor/all'),
  listCursorWorkspaces: () => get<{ workspaces: string[] }>('/ingest/cursor/workspaces'),
  getSettings: () => get<import('../types').Settings>('/settings'),
  saveSettings: (body: Partial<import('../types').Settings> & { llm_api_key?: string }) =>
    post('/settings', body),
  quizHistory: (limit = 50) =>
    get<import('../types').HistoryItem[]>(`/study/history?content_type=quiz&limit=${limit}`),
  guideHistory: (limit = 50) =>
    get<import('../types').HistoryItem[]>(`/study/history?content_type=study_guide&limit=${limit}`),
  generateSummary: (period: import('../types').Period) =>
    `${BASE}/summary/generate/${period}`,
}
