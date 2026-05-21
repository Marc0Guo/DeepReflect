import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

export type DomainRegionData = {
  label: string
  color: string
  topicCount: number
}

export type TopicNodeData = {
  label: string
  askCount: number
  weakScore: number
  category: string
  color: string
  radius: number
  /** Matches the nodeWidth/nodeHeight from TopicPlacement — used for consistent sizing */
  nodeWidth: number
  nodeHeight: number
  dimmed?: boolean
  highlighted?: boolean
}

export const DomainRegionNode = memo(function DomainRegionNode({ data }: NodeProps) {
  const d = data as DomainRegionData
  return (
    <div
      className="domain-region"
      style={{ ['--region-color' as string]: d.color }}
    >
      <div className="domain-region__pill">{d.label}</div>
      <span className="domain-region__count">{d.topicCount} topics</span>
    </div>
  )
})

export const TopicNode = memo(function TopicNode({ data }: NodeProps) {
  const d = data as TopicNodeData
  const size = d.radius * 2

  return (
    <div
      className={`topic-node${d.highlighted ? ' topic-node--hi' : ''}${d.dimmed ? ' topic-node--dim' : ''}`}
      style={{
        width: d.nodeWidth,
        height: d.nodeHeight,
        ['--topic-color' as string]: d.color,
      }}
    >
      <Handle type="target" position={Position.Top} className="graph-handle" />
      <Handle type="source" position={Position.Bottom} className="graph-handle" />
      <div
        className="topic-node__circle"
        style={{
          width: size,
          height: size,
          borderColor: d.color,
          boxShadow: d.highlighted
            ? `0 0 0 3px color-mix(in srgb, ${d.color} 35%, transparent)`
            : undefined,
        }}
      >
        <span className="topic-node__count">{d.askCount}</span>
      </div>
      <div className="topic-node__label" title={d.label} style={{ maxWidth: d.nodeWidth - 8 }}>
        {d.label}
      </div>
    </div>
  )
})
