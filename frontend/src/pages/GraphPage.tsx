import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { GraphLegend, GraphView } from '../components/KnowledgeGraph/GraphView'
import type { ConversationTurn, GraphData } from '../types'

export function GraphPage() {
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)
  const [selected, setSelected] = useState<{ id: string; label: string } | null>(null)
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [turnsLoading, setTurnsLoading] = useState(false)

  async function loadGraph() {
    setLoading(true)
    try {
      setGraph(await api.graph())
    } catch {
      setGraph({ nodes: [], edges: [] })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadGraph() }, [])

  async function handleReset() {
    if (!window.confirm(
      'Clear all topic tags and the knowledge graph?\n\nImported conversations stay — run Analysis again to rebuild with domain hubs (Web, Data, ML…).',
    )) return
    setResetting(true)
    try {
      await api.resetAnalysis()
      setSelected(null)
      setTurns([])
      await loadGraph()
    } finally {
      setResetting(false)
    }
  }

  async function handleNodeClick(nodeId: string, label: string) {
    setSelected({ id: nodeId, label })
    setTurnsLoading(true)
    try {
      setTurns(await api.conceptTurns(Number(nodeId)))
    } catch {
      setTurns([])
    }
    setTurnsLoading(false)
  }

  const topicCount = graph.nodes.filter((n) => n.node_type !== 'domain').length
  const domainCount = new Set(
    graph.nodes.filter((n) => n.node_type !== 'domain').map((n) => n.category),
  ).size

  return (
    <div className="flex h-full">
      <div className="flex-1 relative">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading graph...</span>
            </div>
          </div>
        ) : <GraphView data={graph} onNodeClick={handleNodeClick} />}

        <div className="absolute top-4 left-4 glass px-5 py-4 animate-fade-in flex flex-col gap-2" style={{ pointerEvents: 'auto' }}>
          <div className="font-display text-sm font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><line x1="8.5" y1="7.5" x2="15.5" y2="16.5"/><line x1="15" y1="6" x2="9" y2="6"/></svg>
            Knowledge Graph
          </div>
          <GraphLegend domainCount={domainCount} topicCount={topicCount} />
          <div className="text-[11px]" style={{ color: 'var(--text-faint)' }}>Scroll to zoom · drag nodes · click topic to explore</div>
          <button
            type="button"
            onClick={handleReset}
            disabled={resetting}
            className="mt-1 text-[11px] font-semibold px-3 py-1.5 rounded-lg cursor-pointer disabled:opacity-50 transition-opacity"
            style={{
              background: 'color-mix(in srgb, var(--accent-warm) 15%, transparent)',
              color: 'var(--accent-warm)',
              border: '1px solid color-mix(in srgb, var(--accent-warm) 35%, transparent)',
            }}
          >
            {resetting ? 'Resetting…' : 'Reset tags & rebuild'}
          </button>
        </div>
      </div>

      {selected && (
        <div className="w-[340px] glass flex flex-col animate-fade-in" style={{ borderRadius: '20px 0 0 20px', borderRight: 'none', margin: '12px 0' }}>
          <div className="p-5" style={{ borderBottom: '1px solid var(--glass-border)' }}>
            <div className="section-label mb-1.5">Selected Concept</div>
            <div className="font-display text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{selected.label}</div>
            <button onClick={() => setSelected(null)} className="mt-3 text-xs flex items-center gap-1 cursor-pointer transition-colors" style={{ color: 'var(--text-faint)' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Close
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {turnsLoading && <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}><div className="w-4 h-4 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />Loading...</div>}
            {!turnsLoading && turns.length === 0 && <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No history found.</p>}
            {turns.map((t) => (
              <div key={t.id} className="space-y-2 animate-fade-in-up">
                <div className="text-[10px] font-medium" style={{ color: 'var(--text-faint)' }}>{new Date(t.timestamp).toLocaleString()} · <span style={{ color: 'color-mix(in srgb, var(--accent) 60%, var(--text-muted))' }}>{t.source}</span></div>
                <div className="glass-subtle p-3.5">
                  <div className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--accent)' }}>You asked</div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{t.user_prompt}</p>
                </div>
                {t.ai_response && (
                  <div className="glass-subtle p-3.5" style={{ opacity: 0.7 }}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-faint)' }}>AI replied</div>
                    <p className="text-xs leading-relaxed line-clamp-4" style={{ color: 'var(--text-muted)' }}>{t.ai_response}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
