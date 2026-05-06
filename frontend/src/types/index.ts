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
