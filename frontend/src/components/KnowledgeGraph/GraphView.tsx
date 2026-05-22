import { useEffect, useRef, useCallback } from 'react'
import * as d3 from 'd3'
import type { GraphData } from '../../types'
import './graph.css'

// ── Color palette ────────────────────────────────────────────────────────────
export const DOMAIN_COLORS: Record<string, string> = {
  web: '#34d399',
  data: '#38bdf8',
  ml: '#a78bfa',
  programming: '#fbbf24',
  infra: '#c084fc',
  mobile: '#22d3ee',
  math: '#facc15',
  general: '#94a3b8',
  other: '#78716c',
}

const DOMAIN_LABELS: Record<string, string> = {
  web: 'Web',
  data: 'Data',
  ml: 'ML / AI',
  programming: 'Programming',
  infra: 'Infra',
  mobile: 'Mobile',
  math: 'Math',
  general: 'General',
  other: 'Other',
}

// ── Simulation types ─────────────────────────────────────────────────────────
interface SimNode extends d3.SimulationNodeDatum {
  id: string
  label: string
  category: string
  isDomain: boolean
  askCount: number
  r: number
  color: string
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  id: string
  edgeType: 'hub' | 'peer' | 'cross'
}

// ── Data helpers ─────────────────────────────────────────────────────────────
function buildSim(data: GraphData): { nodes: SimNode[]; links: SimLink[] } {
  const nodeIndex = new Map<string, SimNode>()

  // Count topics per domain for sizing
  const domainTopicCount = new Map<string, number>()
  for (const n of data.nodes) {
    if (n.node_type !== 'domain') {
      domainTopicCount.set(n.category, (domainTopicCount.get(n.category) ?? 0) + 1)
    }
  }

  // Only keep domains that have topics
  const activeDomains = new Set(
    data.edges
      .filter((e) => e.edge_type === 'hub')
      .flatMap((e) => [e.source, e.target]),
  )

  for (const n of data.nodes) {
    if (n.node_type === 'domain' && !activeDomains.has(n.id)) continue
    const color = DOMAIN_COLORS[n.category] ?? '#94a3b8'
    const isDomain = n.node_type === 'domain'
    const count = isDomain
      ? (domainTopicCount.get(n.category) ?? 0)
      : n.ask_count
    const r = isDomain
      ? Math.max(20, Math.min(42, 18 + Math.sqrt(count) * 4.5))
      : Math.max(7, Math.min(16, 6 + Math.sqrt(Math.max(1, count)) * 2.2))

    const sim: SimNode = {
      id: n.id,
      label: isDomain ? (DOMAIN_LABELS[n.category] ?? n.label) : n.label,
      category: n.category,
      isDomain,
      askCount: n.ask_count,
      r,
      color,
    }
    nodeIndex.set(n.id, sim)
  }

  const nodes = Array.from(nodeIndex.values())
  const ids = new Set(nodes.map((n) => n.id))

  const links: SimLink[] = data.edges
    .filter(
      (e) =>
        e.edge_type !== undefined &&
        ids.has(e.source) &&
        ids.has(e.target) &&
        e.source !== e.target,
    )
    .map((e, i) => ({
      id: `l-${i}`,
      source: e.source,
      target: e.target,
      edgeType: e.edge_type as 'hub' | 'peer' | 'cross',
    }))

  return { nodes, links }
}

// ── Component ────────────────────────────────────────────────────────────────
interface Props {
  data: GraphData
  onNodeClick?: (nodeId: string, label: string) => void
}

export function GraphView({ data, onNodeClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const gRef = useRef<SVGGElement>(null)
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null)
  const onClickRef = useRef(onNodeClick)

  useEffect(() => {
    onClickRef.current = onNodeClick
  }, [onNodeClick])

  const init = useCallback(() => {
    const svgEl = svgRef.current
    const gEl = gRef.current
    if (!svgEl || !gEl) return

    // Stop previous simulation
    simRef.current?.stop()
    d3.select(gEl).selectAll('*').remove()
    d3.select(svgEl).on('.zoom', null)

    const { nodes, links } = buildSim(data)
    if (!nodes.length) return

    const W = svgEl.clientWidth || 900
    const H = svgEl.clientHeight || 600

    const svg = d3.select(svgEl)
    const g = d3.select(gEl)

    // ── Pre-position: domains in a circle, topics around their domain ────────
    // This prevents the "cold start from origin" sun-spoke artifact.
    const domainNodes = nodes.filter((n) => n.isDomain)
    const topicsByCategory = new Map<string, SimNode[]>()
    nodes.filter((n) => !n.isDomain).forEach((t) => {
      if (!topicsByCategory.has(t.category)) topicsByCategory.set(t.category, [])
      topicsByCategory.get(t.category)!.push(t)
    })
    const nDomains = domainNodes.length
    domainNodes.forEach((d, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, nDomains) - Math.PI / 2
      const radius = Math.min(W, H) * 0.1   // start domains close together
      d.x = W / 2 + radius * Math.cos(angle)
      d.y = H / 2 + radius * Math.sin(angle)
      const topics = topicsByCategory.get(d.category) ?? []
      topics.forEach((t, j) => {
        const ta = angle + (2 * Math.PI * j) / Math.max(1, topics.length)
        const tr = 45 + Math.random() * 20
        t.x = d.x! + tr * Math.cos(ta)
        t.y = d.y! + tr * Math.sin(ta)
      })
    })

    // ── Simulation ───────────────────────────────────────────────────────────
    const sim = d3.forceSimulation<SimNode, SimLink>(nodes)
      .force(
        'link',
        d3.forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance((l) =>
            l.edgeType === 'hub' ? 80 : l.edgeType === 'peer' ? 80 : 110,
          )
          .strength((l) =>
            l.edgeType === 'hub' ? 0.7 : l.edgeType === 'peer' ? 0.2 : 0.15,
          ),
      )
      .force(
        'charge',
        d3.forceManyBody<SimNode>().strength((d) => (d.isDomain ? -50 : -20)),
      )
      .force('center', d3.forceCenter(W / 2, H / 2).strength(0.08))
      .force(
        'collide',
        d3.forceCollide<SimNode>((d) => d.r + 6).strength(0.9),
      )

    simRef.current = sim

    // ── Edges ────────────────────────────────────────────────────────────────
    const linkSel = g
      .append('g')
      .attr('class', 'edges')
      .selectAll<SVGLineElement, SimLink>('line')
      .data(links)
      .join('line')
      .attr('class', (l) => `edge edge--${l.edgeType}`)
      .attr('stroke', (l) => {
        const src = l.source as SimNode
        return l.edgeType === 'cross'
          ? '#a78bfa'
          : DOMAIN_COLORS[src.category] ?? '#94a3b8'
      })
      .attr('stroke-width', (l) =>
        l.edgeType === 'hub' ? 1.5 : l.edgeType === 'peer' ? 1 : 1.2,
      )
      .attr('stroke-opacity', (l) =>
        l.edgeType === 'hub' ? 0.60 : l.edgeType === 'peer' ? 0.20 : 0.55,
      )
      .attr('stroke-dasharray', (l) =>
        l.edgeType === 'cross' ? '6 4' : l.edgeType === 'peer' ? '3 4' : null,
      )

    // ── Nodes ────────────────────────────────────────────────────────────────
    const nodeSel = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll<SVGGElement, SimNode>('g')
      .data(nodes, (d) => d.id)
      .join('g')
      .attr('class', (d) => `node ${d.isDomain ? 'node--domain' : 'node--topic'}`)
      .style('cursor', (d) => (d.isDomain ? 'default' : 'pointer'))

    // Glow circle (blurred behind for domain nodes)
    nodeSel
      .filter((d) => d.isDomain)
      .append('circle')
      .attr('r', (d) => d.r + 8)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', 0.08)
      .attr('filter', 'url(#glow-soft)')
      .attr('pointer-events', 'none')

    // Main circle
    nodeSel
      .append('circle')
      .attr('class', 'node__circle')
      .attr('r', (d) => d.r)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', (d) => (d.isDomain ? 0.22 : 0.14))
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', (d) => (d.isDomain ? 2.5 : 1.5))
      .attr('stroke-opacity', (d) => (d.isDomain ? 0.9 : 0.65))

    // Label
    nodeSel
      .append('text')
      .attr('class', 'node__label')
      .attr('dy', (d) => d.r + (d.isDomain ? 16 : 13))
      .attr('text-anchor', 'middle')
      .attr('font-size', (d) => (d.isDomain ? '12px' : '10px'))
      .attr('font-weight', (d) => (d.isDomain ? '700' : '500'))
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', (d) => (d.isDomain ? 0.95 : 0.72))
      .attr('letter-spacing', (d) => (d.isDomain ? '0.05em' : '0'))
      .text((d) => d.label)
      .attr('pointer-events', 'none')

    // ── Tick ─────────────────────────────────────────────────────────────────
    sim.on('tick', () => {
      linkSel
        .attr('x1', (l) => (l.source as SimNode).x!)
        .attr('y1', (l) => (l.source as SimNode).y!)
        .attr('x2', (l) => (l.target as SimNode).x!)
        .attr('y2', (l) => (l.target as SimNode).y!)

      nodeSel.attr('transform', (d) => `translate(${d.x!},${d.y!})`)
    })

    // ── Drag ─────────────────────────────────────────────────────────────────
    const drag = d3
      .drag<SVGGElement, SimNode>()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0)
        d.fx = null
        d.fy = null
      })

    nodeSel.call(drag)

    // ── Zoom ─────────────────────────────────────────────────────────────────
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.08, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)
    // Run enough ticks so the layout settles before the first paint
    sim.tick(300)
    const padding = 80
    const xs = nodes.map((n) => n.x!)
    const ys = nodes.map((n) => n.y!)
    const xMin = Math.min(...xs) - padding
    const xMax = Math.max(...xs) + padding
    const yMin = Math.min(...ys) - padding
    const yMax = Math.max(...ys) + padding
    const scale = Math.min(1.1, Math.min(W / (xMax - xMin), H / (yMax - yMin)))
    const tx = (W - scale * (xMin + xMax)) / 2
    const ty = (H - scale * (yMin + yMax)) / 2
    svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))

    // ── Hover ────────────────────────────────────────────────────────────────
    nodeSel
      .on('mouseenter', function (_, d) {
        if (d.isDomain) return
        const connected = new Set<string>([d.id])
        links.forEach((l) => {
          const src = (l.source as SimNode).id
          const tgt = (l.target as SimNode).id
          if (src === d.id) connected.add(tgt)
          if (tgt === d.id) connected.add(src)
        })
        nodeSel.classed('node--dim', (n) => !connected.has(n.id))
        nodeSel.classed('node--hi', (n) => connected.has(n.id))
        linkSel.classed('edge--dim', (l) => {
          const src = (l.source as SimNode).id
          const tgt = (l.target as SimNode).id
          return src !== d.id && tgt !== d.id
        })
        linkSel.classed('edge--hi', (l) => {
          const src = (l.source as SimNode).id
          const tgt = (l.target as SimNode).id
          return src === d.id || tgt === d.id
        })
        // Highlight the hovered node itself
        d3.select(this).select('.node__circle').attr('fill-opacity', 0.35).attr('stroke-opacity', 1)
      })
      .on('mouseleave', function (_, d) {
        if (d.isDomain) return
        nodeSel.classed('node--dim node--hi', false)
        linkSel.classed('edge--dim edge--hi', false)
        d3.select(this)
          .select('.node__circle')
          .attr('fill-opacity', 0.14)
          .attr('stroke-opacity', 0.65)
      })
      .on('click', (_, d) => {
        if (!d.isDomain) onClickRef.current?.(d.id, d.label)
      })
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    init()
    return () => {
      simRef.current?.stop()
    }
  }, [init])

  const topicCount = data.nodes.filter((n) => n.node_type !== 'domain').length

  if (!topicCount) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          style={{ color: 'var(--text-faint)' }}
        >
          <circle cx="6" cy="6" r="3" />
          <circle cx="18" cy="18" r="3" />
          <circle cx="18" cy="6" r="3" />
          <line x1="8.5" y1="7.5" x2="15.5" y2="16.5" />
          <line x1="15" y1="6" x2="9" y2="6" />
        </svg>
        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
          No graph data yet.
        </div>
        <div className="text-xs" style={{ color: 'var(--text-faint)' }}>
          Import conversations and run analysis first.
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full obsidian-graph">
      <svg ref={svgRef} width="100%" height="100%" style={{ display: 'block' }}>
        <defs>
          <filter id="glow-soft" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
          </filter>
          <filter id="glow-hi" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g ref={gRef} />
      </svg>

    </div>
  )
}

// Kept for GraphPage.tsx compatibility
export function GraphLegend({
  domainCount,
  topicCount,
}: {
  domainCount: number
  topicCount: number
}) {
  return (
    <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
      <span
        className="tabular-nums font-semibold"
        style={{ color: 'var(--accent)' }}
      >
        {domainCount}
      </span>{' '}
      domains
      <span className="mx-1.5" style={{ color: 'var(--text-faint)' }}>
        /
      </span>
      <span
        className="tabular-nums font-semibold"
        style={{ color: 'var(--accent-secondary)' }}
      >
        {topicCount}
      </span>{' '}
      topics
    </div>
  )
}
