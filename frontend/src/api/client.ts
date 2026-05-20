const BASE = '/api'

function buildAnalyzeParams(selection: import('../types').AnalyzeSelection): URLSearchParams {
  const p = new URLSearchParams()
  p.set('mode', selection.mode)
  if (selection.mode === 'recent' && selection.limit != null) {
    p.set('limit', String(selection.limit))
  }
  if (selection.mode === 'range') {
    if (selection.since) p.set('since', selection.since)
    if (selection.until) p.set('until', selection.until)
  }
  return p
}

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
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const err = (await res.json()) as { detail?: string }
      if (typeof err.detail === 'string') message = err.detail
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(message)
  }
  return res.json()
}

export const api = {
  stats: (filters?: import('../types').DashboardFilters) =>
    get<import('../types').Stats>(`/summary/stats${buildFilterQuery(filters)}`),
  dashboardAnalytics: (filters?: import('../types').DashboardFilters) => {
    const p = new URLSearchParams()
    appendFilterParams(p, filters)
    const qs = p.toString()
    return get<import('../types').DashboardAnalytics>(`/summary/analytics${qs ? `?${qs}` : ''}`)
  },
  dashboardInsights: (
    filters?: import('../types').DashboardFilters,
    year?: number,
  ) => {
    const p = new URLSearchParams()
    appendFilterParams(p, filters)
    if (year != null) p.set('year', String(year))
    const qs = p.toString()
    return get<import('../types').DashboardInsights>(`/summary/insights${qs ? `?${qs}` : ''}`)
  },
  threadTurns: (sessionId: string, source: string, limit = 40) =>
    get<import('../types').ThreadTurn[]>(
      `/summary/thread-turns?session_id=${encodeURIComponent(sessionId)}&source=${encodeURIComponent(source)}&limit=${limit}`,
    ),
  graph: () => get<import('../types').GraphData>('/graph'),
  concepts: (minAsk = 1, filters?: import('../types').DashboardFilters) => {
    const p = new URLSearchParams({ min_ask_count: String(minAsk) })
    appendFilterParams(p, filters)
    return get<import('../types').Concept[]>(`/graph/concepts?${p}`)
  },
  conceptTurns: (id: number, limit = 20) =>
    get<import('../types').ConversationTurn[]>(`/graph/concept/${id}/turns?limit=${limit}`),
  flashcards: () => get<import('../types').Flashcard[]>('/study/flashcards'),
  generateFlashcards: (limit = 10, conceptId?: number) =>
    post<{ generated: number; detail: string | null }>('/study/flashcards/generate', {
      limit,
      ...(conceptId != null ? { concept_id: conceptId } : {}),
    }),
  studyGuide: (period = 'this week') => get<{ guide: string }>(`/study/guide?period=${period}`),
  quiz: () => get<{ questions: import('../types').QuizQuestion[] }>('/study/quiz'),
  analyzeBounds: () => get<import('../types').AnalyzeBounds>('/analyze/bounds'),
  analyze: (selection: import('../types').AnalyzeSelection) => {
    const p = buildAnalyzeParams(selection)
    const qs = p.toString()
    return post<{ processed: number; errors: number; remaining: number }>(
      `/analyze${qs ? `?${qs}` : ''}`,
    )
  },
  analyzePreview: (selection: import('../types').AnalyzeSelection) => {
    const p = buildAnalyzeParams(selection)
    const qs = p.toString()
    return get<import('../types').AnalyzePreview>(`/analyze/preview${qs ? `?${qs}` : ''}`)
  },
  analyzeStream: (
    selection: import('../types').AnalyzeSelection,
    onProgress: (event: import('../types').AnalyzeProgress) => void,
  ): Promise<import('../types').AnalyzeResult> =>
    new Promise((resolve, reject) => {
      const p = buildAnalyzeParams(selection)
      const qs = p.toString()
      fetch(`${BASE}/analyze/stream${qs ? `?${qs}` : ''}`, { method: 'POST' })
        .then(async (res) => {
          if (!res.ok) {
            const err = await res.text()
            throw new Error(err || `${res.status} ${res.statusText}`)
          }
          const reader = res.body?.getReader()
          if (!reader) throw new Error('No response body')
          const decoder = new TextDecoder()
          let buffer = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() ?? ''
            for (const line of lines) {
              if (!line.trim()) continue
              const event = JSON.parse(line) as import('../types').AnalyzeProgress
              onProgress(event)
              if (event.stage === 'done') {
                resolve({
                  processed: event.processed ?? 0,
                  errors: event.errors ?? 0,
                  remaining: event.remaining ?? 0,
                })
              }
            }
          }
          reject(new Error('Analysis stream ended without completion'))
        })
        .catch(reject)
    }),
  ingestAll: () => post<import('../types').IngestResult>('/ingest/claude-code/all'),
  listProjects: () => get<{ projects: string[] }>('/ingest/projects'),
  ingestCursor: () => post<import('../types').IngestResult>('/ingest/cursor/all'),
  ingestCursorStream: (
    onProgress: (event: import('../types').CursorImportProgress) => void,
  ): Promise<import('../types').IngestResult> =>
    new Promise((resolve, reject) => {
      fetch(`${BASE}/ingest/cursor/all/stream`, { method: 'POST' })
        .then(async (res) => {
          if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
          const reader = res.body?.getReader()
          if (!reader) throw new Error('No response body')
          const decoder = new TextDecoder()
          let buffer = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() ?? ''
            for (const line of lines) {
              if (!line.trim()) continue
              const event = JSON.parse(line) as import('../types').CursorImportProgress
              onProgress(event)
              if (event.stage === 'done') {
                resolve({
                  imported: event.imported ?? 0,
                  new: event.new ?? 0,
                  source: 'cursor',
                })
              }
            }
          }
          reject(new Error('Import stream ended without completion'))
        })
        .catch(reject)
    }),
  clearMemory: () => post<{ cleared: Record<string, number> }>('/ingest/clear'),
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
  notificationStatus: () => get<import('../types').NotificationStatus>('/notifications/status'),
  testNotification: (platform: string) =>
    post<{ platform: string; result: string }>(`/notifications/test/${platform}`),
  sendNotificationNow: () => post<{ results: Record<string, string> }>('/notifications/send-now'),
  reloadSchedule: () => post('/notifications/reload-schedule'),
}
