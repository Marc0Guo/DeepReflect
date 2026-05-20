export interface Concept {
  id: number
  name: string
  category: string
  ask_count: number
  weak_score: number
  last_seen: string | null
  first_seen?: string | null
}

export interface GraphNode {
  id: string
  label: string
  category: string
  ask_count: number
  weak_score: number
  last_seen: string | null
}

export interface GraphEdge {
  source: string
  target: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface ConversationTurn {
  id: number
  timestamp: string
  user_prompt: string
  ai_response: string
  source: string
  cwd: string
}

export interface Stats {
  total_turns: number
  total_concepts: number
  total_flashcards: number
  weekly_turns: number
  period_turns: number
  sources: Record<string, number>
  available_sources: string[]
  filters_active: boolean
  last_updated: string | null
  coverage_days: number
  history_start: string | null
  history_end: string | null
  longest_streak_days: number
  total_duration_seconds: number
  category_count: number | null
  filtered_exchanges: number
  filtered_tokens?: number
}

export interface IngestResult {
  imported: number
  new: number
  source: string
}

export interface CursorImportProgress {
  stage: 'discover' | 'import' | 'parsed' | 'saving' | 'done'
  progress: number
  message: string
  imported?: number
  new?: number
}

export type AnalyzeMode = 'recent' | 'period'

export interface AnalyzeBounds {
  total_unanalyzed: number
  date_min: string | null
  date_max: string | null
  recent_limit_min: number
  recent_limit_max: number
  recent_limit_default: number
}

export interface AnalyzeSelection {
  mode: 'recent' | 'range'
  limit?: number
  since?: string
  until?: string
}

export interface AnalyzePreview {
  total_unanalyzed: number
  in_selection: number
  to_process: number
  limit: number | null
  since: string | null
  until: string | null
  summary: string
  detail: string
}

export interface AnalyzeProgress {
  stage: 'start' | 'progress' | 'done'
  progress: number
  message: string
  total?: number
  current?: number
  processed?: number
  errors?: number
  remaining?: number
}

export interface AnalyzeResult {
  processed: number
  errors: number
  remaining: number
}

export type DashboardPeriod = 'all' | 'day' | 'week' | 'month' | 'year'
export type DashboardStatus = 'all' | 'weak' | 'solved'

export interface DashboardFilters {
  period: DashboardPeriod
  source: string
  concept: string
  status: DashboardStatus
}

export interface ActivityPoint {
  date: string
  count: number
}

export interface TopicSlice {
  name: string
  count: number
  category: string
}

export interface CategorySlice {
  name: string
  count: number
  color: string
}

export interface DashboardAnalytics {
  days: number
  activity: ActivityPoint[]
  topics: TopicSlice[]
  categories: CategorySlice[]
}

export interface CalendarDay {
  date: string
  count: number
  cursor: number
  claude: number
}

export interface HeatmapCell {
  dow: number
  hour: number
  count: number
  cursor: number
  claude: number
}

export interface SessionDepthBucket {
  bucket: string
  count: number
}

export interface ThreadSummary {
  label: string
  short_label: string
  source: string
  session_id: string
  count: number
}

export interface ThreadTurn {
  id: number
  timestamp: string
  user_prompt: string
  ai_response: string
  source: string
}

export interface DashboardInsights {
  calendar_years?: number[]
  calendar_year?: number
  calendar?: CalendarDay[]
  calendar_max?: number
  time_heatmap?: HeatmapCell[]
  time_heatmap_max?: number
  word_cloud?: { text: string; count: number; weight: number }[]
}

export interface Flashcard {
  id: number
  front: string
  back: string
  concept_id: number | null
}

export type Period = 'daily' | 'weekly' | 'monthly' | 'yearly'

export interface Settings {
  llm_provider: string
  llm_api_key_masked: string
  llm_api_key_set: boolean
  llm_model: string
  llm_base_url: string
  intervention_tone: string
  repeat_threshold: number
  port: number
  data_dir: string
  notify_enabled: boolean
  notify_time: string
  notify_channels: string[]
  discord_webhook_url: string
  slack_webhook_url: string
  slack_bot_token_set: boolean
  imessage_recipient: string
  wechat_recipient: string
}

export interface NotificationStatus {
  enabled: boolean
  notify_time: string
  channels: string[]
  next_fire_time: string | null
  last_sent: string | null
}

export interface HistoryItem {
  id: number
  content_type: 'quiz' | 'study_guide'
  title: string
  period: string
  created_at: string
  questions?: QuizQuestion[]
  content?: string
}

export interface QuizChoice {
  text: string
  is_correct: boolean
  explanation: string
}

export interface QuizQuestion {
  question: string
  type: 'multiple_choice' | 'short_answer'
  choices?: QuizChoice[]
  answer?: string
  explanation?: string
}
