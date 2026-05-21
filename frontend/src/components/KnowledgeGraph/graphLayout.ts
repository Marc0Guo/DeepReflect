import type { GraphNode } from '../../types'

export const DOMAIN_COLORS: Record<string, string> = {
  web: '#30d158',
  data: '#0ea5e9',
  ml: '#a855f7',
  programming: '#f59e0b',
  infra: '#a78bfa',
  mobile: '#38bdf8',
  math: '#eab308',
  general: '#94a3b8',
  other: '#78716c',
}

export const DOMAIN_LABELS: Record<string, string> = {
  web: 'Web',
  data: 'Data',
  ml: 'ML & AI',
  programming: 'Programming',
  infra: 'Infra & DevOps',
  mobile: 'Mobile',
  math: 'Math',
  general: 'General',
  other: 'Other',
}

const ORIGIN_X = 48
const ORIGIN_Y = 60
const REGION_GAP_Y = 80
const REGION_PAD_X = 40
const REGION_PAD_TOP = 50   // room for the pill label above content
const REGION_PAD_BOTTOM = 24
const CELL_GAP = 24         // gap between topic cells
const NODE_MIN_R = 20
const NODE_MAX_R = 32
const LABEL_H = 32          // height reserved below circle for label

export function topicRadius(askCount: number): number {
  return Math.min(NODE_MAX_R, NODE_MIN_R + Math.sqrt(Math.max(1, askCount)) * 3.5)
}

/** Returns the bounding box a single topic node will occupy (= React Flow node size) */
export function topicFootprint(askCount: number, label: string): {
  r: number
  w: number
  h: number
} {
  const r = topicRadius(askCount)
  // width: enough to show the label text without hard-wrapping (capped at 140)
  const w = Math.min(140, Math.max(r * 2 + 16, 48 + label.length * 5.2))
  const h = r * 2 + LABEL_H
  return { r, w, h }
}

export type LayoutRegion = {
  id: string
  category: string
  label: string
  color: string
  x: number
  y: number
  width: number
  height: number
  topics: GraphNode[]
}

export type TopicPlacement = {
  node: GraphNode
  regionId: string
  /** position relative to the parent region node */
  x: number
  y: number
  radius: number
  nodeWidth: number
  nodeHeight: number
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function placeTopicsInRegion(
  group: GraphNode[],
  regionId: string,
  innerW: number,
  innerH: number,
): TopicPlacement[] {
  const sorted = [...group].sort((a, b) => a.label.localeCompare(b.label))
  const footprints = sorted.map((t) => ({ t, ...topicFootprint(t.ask_count, t.label) }))
  const placements: TopicPlacement[] = []

  if (group.length <= 6) {
    // Ring layout for small groups
    const maxW = Math.max(...footprints.map((f) => f.w))
    const count = footprints.length
    const chord = maxW + CELL_GAP
    const ringR = count <= 1 ? 0 : Math.max(75, chord / (2 * Math.sin(Math.PI / count)))
    const cx = innerW / 2
    const cy = innerH / 2

    footprints.forEach((fp, j) => {
      const angle = (2 * Math.PI * j) / count - Math.PI / 2
      placements.push({
        node: fp.t,
        regionId,
        x: cx + ringR * Math.cos(angle) - fp.w / 2,
        y: cy + ringR * Math.sin(angle) - fp.h / 2,
        radius: fp.r,
        nodeWidth: fp.w,
        nodeHeight: fp.h,
      })
    })
    return placements
  }

  // Grid layout for larger groups
  const cols = Math.min(5, Math.max(2, Math.ceil(Math.sqrt(group.length * 1.2))))
  const rows = Math.ceil(group.length / cols)
  const cellW = (innerW - CELL_GAP) / cols
  const cellH = (innerH - CELL_GAP) / rows

  footprints.forEach((fp, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    placements.push({
      node: fp.t,
      regionId,
      x: col * cellW + (cellW - fp.w) / 2 + CELL_GAP / 2,
      y: row * cellH + (cellH - fp.h) / 2 + CELL_GAP / 2,
      radius: fp.r,
      nodeWidth: fp.w,
      nodeHeight: fp.h,
    })
  })

  return placements
}

function measureRegion(group: GraphNode[]): {
  width: number
  height: number
  placements: TopicPlacement[]
  regionId: string
} {
  const category = group[0]?.category || 'general'
  const regionId = `region-${category}`
  const footprints = group.map((t) => topicFootprint(t.ask_count, t.label))
  const maxFw = Math.max(...footprints.map((f) => f.w), 100)
  const maxFh = Math.max(...footprints.map((f) => f.h), 60)

  let innerW: number
  let innerH: number

  if (group.length <= 6) {
    const count = group.length
    const chord = maxFw + CELL_GAP
    const ringR = count <= 1 ? 80 : Math.max(80, chord / (2 * Math.sin(Math.PI / count)))
    innerW = ringR * 2 + maxFw + 32
    innerH = ringR * 2 + maxFh + 24
  } else {
    const cols = Math.min(5, Math.max(2, Math.ceil(Math.sqrt(group.length * 1.2))))
    const rows = Math.ceil(group.length / cols)
    innerW = cols * (maxFw + CELL_GAP) + CELL_GAP
    innerH = rows * (maxFh + CELL_GAP) + CELL_GAP
  }

  const width = innerW + REGION_PAD_X * 2
  const height = innerH + REGION_PAD_TOP + REGION_PAD_BOTTOM

  const raw = placeTopicsInRegion(group, regionId, innerW, innerH)
  // Offset placements by region padding so they're correctly inside the region
  const placements: TopicPlacement[] = raw.map((p) => ({
    ...p,
    x: p.x + REGION_PAD_X,
    y: p.y + REGION_PAD_TOP,
  }))

  return { width, height, placements, regionId }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function buildMapLayout(nodes: GraphNode[]): {
  regions: LayoutRegion[]
  placements: TopicPlacement[]
} {
  const hubs = nodes
    .filter((n) => n.node_type === 'domain')
    .sort((a, b) => a.label.localeCompare(b.label))

  const topicsByCategory = new Map<string, GraphNode[]>()
  for (const t of nodes.filter((n) => n.node_type !== 'domain')) {
    const cat = t.category || 'general'
    if (!topicsByCategory.has(cat)) topicsByCategory.set(cat, [])
    topicsByCategory.get(cat)!.push(t)
  }

  const regions: LayoutRegion[] = []
  const allPlacements: TopicPlacement[] = []

  // Sort hubs so the largest domain appears first (most visual weight at top)
  const specsUnsorted = hubs
    .map((hub) => {
      const group = topicsByCategory.get(hub.category) ?? []
      if (group.length === 0) return null
      const m = measureRegion(group)
      return { hub, group, ...m }
    })
    .filter(Boolean) as Array<{
      hub: GraphNode
      group: GraphNode[]
      width: number
      height: number
      placements: TopicPlacement[]
      regionId: string
    }>

  // Largest domain first so it gets the most prominent position
  const specs = [...specsUnsorted].sort((a, b) => b.group.length - a.group.length)

  // Canvas width = widest region (all regions are horizontally centered within it)
  const canvasW = Math.max(...specs.map((s) => s.width), 420) + ORIGIN_X * 2
  let cursorY = ORIGIN_Y

  for (const spec of specs) {
    const x = (canvasW - spec.width) / 2
    const y = cursorY

    regions.push({
      id: spec.regionId,
      category: spec.hub.category,
      label: spec.hub.label || DOMAIN_LABELS[spec.hub.category] || spec.hub.category,
      color: DOMAIN_COLORS[spec.hub.category] ?? '#94a3b8',
      x,
      y,
      width: spec.width,
      height: spec.height,
      topics: spec.group,
    })

    allPlacements.push(...spec.placements)
    cursorY += spec.height + REGION_GAP_Y
  }

  return { regions, placements: allPlacements }
}
