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
  sources: Record<string, number>
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
