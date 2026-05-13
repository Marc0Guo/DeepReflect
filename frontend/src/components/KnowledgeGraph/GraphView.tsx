import { useCallback, useMemo } from 'react'
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, type Node, type Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { GraphData, GraphNode } from '../../types'

const CAT_COLORS: Record<string, string> = {
  python: '#64d2ff', ml: '#bf5af2', git: '#ff9f0a', web: '#30d158', data: '#64d2ff', math: '#ff9f0a', general: '#98989d', other: '#98989d',
}

function isDark() { return document.documentElement.getAttribute('data-theme') !== 'light' }

function toFlowNodes(graphNodes: GraphNode[]): Node[] {
  const dark = isDark()
  const cols = Math.ceil(Math.sqrt(graphNodes.length))
  return graphNodes.map((n, i) => ({
    id: n.id,
    position: { x: (i % cols) * 200 + Math.random() * 50, y: Math.floor(i / cols) * 180 + Math.random() * 50 },
    data: { label: n.label, askCount: n.ask_count, weakScore: n.weak_score, category: n.category },
    style: {
      background: dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.30)',
      backdropFilter: 'blur(16px) saturate(200%)',
      WebkitBackdropFilter: 'blur(16px) saturate(200%)',
      border: `1px solid ${n.weak_score >= 0.4
        ? (dark ? 'rgba(255,55,95,0.7)' : 'rgba(255,45,85,0.6)')
        : (CAT_COLORS[n.category] ?? 'rgba(255,255,255,0.20)')}`,
      borderRadius: 14, color: dark ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.8)',
      fontSize: 12, fontFamily: 'Outfit, system-ui', fontWeight: n.ask_count > 3 ? 700 : 500,
      padding: '8px 14px', minWidth: 90,
      boxShadow: dark ? '0 2px 12px rgba(0,0,0,0.25)' : '0 2px 12px rgba(0,0,0,0.06)',
    },
  }))
}

function toFlowEdges(edges: GraphData['edges']): Edge[] {
  const dark = isDark()
  return edges.map((e, i) => ({
    id: `e-${i}`, source: e.source, target: e.target,
    style: { stroke: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)', strokeWidth: Math.min(e.weight, 4) },
  }))
}

interface Props { data: GraphData; onNodeClick?: (nodeId: string, label: string) => void }

export function GraphView({ data, onNodeClick }: Props) {
  const initialNodes = useMemo(() => toFlowNodes(data.nodes), [data.nodes])
  const initialEdges = useMemo(() => toFlowEdges(data.edges), [data.edges])
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)
  const dark = isDark()

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => { onNodeClick?.(node.id, String(node.data.label)) }, [onNodeClick])

  if (!data.nodes.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text-faint)' }}><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><line x1="8.5" y1="7.5" x2="15.5" y2="16.5"/><line x1="15" y1="6" x2="9" y2="6"/></svg>
        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>No graph data yet.</div>
        <div className="text-xs" style={{ color: 'var(--text-faint)' }}>Import conversations and run analysis first.</div>
      </div>
    )
  }

  return (
    <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={handleNodeClick} fitView style={{ background: 'transparent' }}>
      <Background color={dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.04)'} gap={40} size={1} />
      <Controls style={{ background: 'var(--glass)', backdropFilter: 'blur(16px) saturate(200%)', WebkitBackdropFilter: 'blur(16px) saturate(200%)', borderRadius: 12, overflow: 'hidden' }} />
      <MiniMap style={{ background: 'var(--glass)', backdropFilter: 'blur(16px) saturate(200%)', WebkitBackdropFilter: 'blur(16px) saturate(200%)', borderRadius: 12 }} nodeColor={(n) => CAT_COLORS[(n.data as { category: string }).category] ?? '#98989d'} maskColor={dark ? 'rgba(8,18,30,0.65)' : 'rgba(205,220,239,0.55)'} />
    </ReactFlow>
  )
}
