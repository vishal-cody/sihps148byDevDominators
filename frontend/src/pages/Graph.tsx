import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap, useNodesState, useEdgesState,
  addEdge, Handle, Position, BackgroundVariant,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { evidenceAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { GitBranch, RefreshCw, Layers } from 'lucide-react'

// Custom node types
function ForensicNode({ data }: any) {
  const icons: Record<string, string> = {
    host: '🖥', process: '⚙', ip: '🌐', persistence: '🔒', file: '📄', user: '👤'
  }
  return (
    <div style={{
      padding: '8px 12px', borderRadius: 8, minWidth: 120,
      background: data.suspicious
        ? 'rgba(239,68,68,0.1)'
        : 'rgba(19,25,41,0.95)',
      border: `2px solid ${data.suspicious ? '#ef4444' : data.color || '#1e2d4a'}`,
      boxShadow: data.suspicious ? '0 0 12px rgba(239,68,68,0.3)' : '0 2px 8px rgba(0,0,0,0.4)',
      textAlign: 'center', fontSize: 11, fontFamily: 'JetBrains Mono, monospace',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: '#1e2d4a' }} />
      <div style={{ fontSize: 18, marginBottom: 4 }}>{icons[data.nodeType] || '•'}</div>
      <div style={{ color: data.suspicious ? '#ef4444' : data.color || '#e2e8f0', fontWeight: 600, whiteSpace: 'pre-line' }}>
        {data.label}
      </div>
      {data.suspicious && (
        <div style={{ fontSize: 9, color: '#ef4444', marginTop: 2 }}>⚠ SUSPICIOUS</div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#1e2d4a' }} />
    </div>
  )
}

const NODE_TYPES = { forensicNode: ForensicNode }

// Auto-layout using a simple grid
function layoutNodes(nodes: any[], edges: any[]) {
  const levels: Record<string, number> = {}
  const cols: Record<number, number> = {}

  // BFS to assign levels
  const roots = nodes.filter(n => !edges.find((e: any) => e.target === n.id))
  roots.forEach(n => { levels[n.id] = 0 })

  let queue = [...roots]
  while (queue.length) {
    const curr = queue.shift()!
    const outgoing = edges.filter((e: any) => e.source === curr.id)
    outgoing.forEach((e: any) => {
      const target = nodes.find(n => n.id === e.target)
      if (target && levels[target.id] === undefined) {
        levels[target.id] = (levels[curr.id] || 0) + 1
        queue.push(target)
      }
    })
  }

  return nodes.map(n => {
    const level = levels[n.id] || 0
    cols[level] = (cols[level] || 0) + 1
    const col = cols[level]
    return { ...n, position: { x: col * 200 - 100, y: level * 140 + 50 } }
  })
}

export default function EvidenceGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [invId, setInvId] = useState('')

  useEffect(() => {
    import('@/services/api').then(({ investigationsAPI }) => {
      investigationsAPI.list().then(r => {
        if (r.data.length > 0) setInvId(r.data[0].id)
      })
    })
  }, [])

  const load = useCallback(async () => {
    if (!invId) return
    setLoading(true)
    try {
      const r = await evidenceAPI.graph(invId)
      const data = r.data
      const laidOut = layoutNodes(data.nodes || [], data.edges || [])
      setNodes(laidOut)
      setEdges(data.edges || [])
      setStats(data.stats || {})
    } finally { setLoading(false) }
  }, [invId])

  useEffect(() => { load() }, [load])

  const onConnect = useCallback((params: any) => setEdges(e => addEdge(params, e)), [setEdges])

  return (
    <Layout>
      <PageHeader
        title="Evidence Graph"
        subtitle="Interactive forensic relationship graph — hosts, processes, network, persistence"
        badge={{ label: `${stats.total_nodes || 0} nodes`, color: '#8b5cf6' }}
        actions={
          <>
            {stats.suspicious_nodes > 0 && (
              <span style={{
                padding: '0.25rem 0.75rem', borderRadius: 100, fontSize: '0.75rem',
                background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)',
              }}>
                ⚠ {stats.suspicious_nodes} suspicious nodes
              </span>
            )}
            <button className="btn-secondary" onClick={load}><RefreshCw size={14} /></button>
          </>
        }
      />

      {/* Legend */}
      <div style={{
        padding: '0.75rem 2rem', display: 'flex', gap: '1.5rem', alignItems: 'center',
        borderBottom: '1px solid var(--color-border)',
        background: 'rgba(8,12,23,0.6)',
      }}>
        {[
          { label: 'Host', color: '#3b82f6', icon: '🖥' },
          { label: 'Process', color: '#8b5cf6', icon: '⚙' },
          { label: 'Network IP', color: '#10b981', icon: '🌐' },
          { label: 'Persistence', color: '#f59e0b', icon: '🔒' },
          { label: 'Suspicious', color: '#ef4444', icon: '⚠' },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
            <span>{item.icon}</span>
            <span style={{ color: item.color }}>{item.label}</span>
          </div>
        ))}
        <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#475569' }}>
          {stats.total_edges || 0} relationships | {stats.total_nodes || 0} entities
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
            <div>
              <div className="spinner" style={{ margin: '0 auto 1rem' }} />
              <p>Building evidence graph...</p>
            </div>
          </div>
        ) : nodes.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
            <div style={{ textAlign: 'center' }}>
              <GitBranch size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
              <p>No graph data. Run an investigation first.</p>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={NODE_TYPES}
            fitView
            style={{ background: '#0a0e1a' }}
            defaultEdgeOptions={{
              style: { stroke: '#1e2d4a', strokeWidth: 1.5 },
              labelStyle: { fill: '#64748b', fontSize: 10 },
              labelBgStyle: { fill: 'rgba(10,14,26,0.8)', stroke: '#1e2d4a' },
            }}
          >
            <Background variant={BackgroundVariant.Dots} color="#1e2d4a" gap={20} size={1} />
            <Controls style={{ background: 'rgba(19,25,41,0.8)', border: '1px solid #1e2d4a', borderRadius: 8 }} />
            <MiniMap
              style={{ background: 'rgba(8,12,23,0.9)', border: '1px solid #1e2d4a' }}
              nodeColor={(n) => n.data?.color || '#475569'}
              maskColor="rgba(8,12,23,0.8)"
            />
          </ReactFlow>
        )}
      </div>
    </Layout>
  )
}
