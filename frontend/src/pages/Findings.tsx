import { useEffect, useState } from 'react'
import { evidenceAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { AlertTriangle, Shield, ChevronDown, ChevronUp, RefreshCw, Filter } from 'lucide-react'

function FindingCard({ f }: { f: any }) {
  const [expanded, setExpanded] = useState(false)
  const sevColors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e'
  }
  const c = sevColors[f.severity] || '#64748b'

  return (
    <div className="glass-card glass-card-hover" style={{
      borderLeft: `3px solid ${c}`, marginBottom: '0.75rem', overflow: 'hidden',
    }}>
      <div style={{ padding: '1rem 1.25rem', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
              <span style={{
                padding: '0.15rem 0.6rem', borderRadius: 100,
                fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase',
                background: `${c}18`, color: c, border: `1px solid ${c}30`,
              }}>{f.severity}</span>
              <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{f.title}</span>
              {f.mitre_technique && (
                <span className="mono" style={{
                  padding: '0.1rem 0.4rem', borderRadius: 4, fontSize: '0.65rem',
                  background: 'rgba(139,92,246,0.1)', color: '#8b5cf6', border: '1px solid rgba(139,92,246,0.2)',
                }}>
                  MITRE {f.mitre_technique}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', color: '#64748b' }}>
              <span>Rule: <strong style={{ color: '#94a3b8' }}>{f.rule_id}</strong></span>
              <span>Category: <strong style={{ color: '#94a3b8' }}>{f.category}</strong></span>
              <span>Confidence: <strong style={{ color: c }}>{(f.confidence * 100).toFixed(0)}%</strong></span>
              <span>Status: <strong style={{ color: f.status === 'open' ? '#ef4444' : '#10b981' }}>{f.status}</strong></span>
            </div>
          </div>
          {expanded ? <ChevronUp size={16} color="#475569" /> : <ChevronDown size={16} color="#475569" />}
        </div>

        {/* Confidence bar */}
        <div style={{ marginTop: '0.6rem', height: 3, background: '#1e2d4a', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${f.confidence * 100}%`, background: c, borderRadius: 2 }} />
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '0 1.25rem 1.25rem', borderTop: '1px solid var(--color-border-subtle)' }}>
          <div style={{ paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                Description
              </div>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.6, whiteSpace: 'pre-line' }}>{f.description}</p>
            </div>
            {f.recommendation && (
              <div style={{
                padding: '0.75rem', borderRadius: 8,
                background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)',
              }}>
                <div style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700, marginBottom: '0.3rem' }}>
                  💡 Recommendation
                </div>
                <p style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5 }}>{f.recommendation}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Findings() {
  const [findings, setFindings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [invId, setInvId] = useState('')
  const [investigations, setInvestigations] = useState<any[]>([])

  useEffect(() => {
    import('@/services/api').then(({ investigationsAPI }) => {
      investigationsAPI.list().then(r => {
        setInvestigations(r.data)
        if (r.data.length > 0) setInvId(r.data[0].id)
      })
    })
  }, [])

  useEffect(() => {
    if (!invId) return
    const load = async () => {
      setLoading(true)
      try {
        const params: any = {}
        if (filter) params.severity = filter
        const r = await evidenceAPI.findings(invId, params)
        setFindings(r.data)
      } finally { setLoading(false) }
    }
    load()
  }, [invId, filter])

  const counts = {
    critical: findings.filter(f => f.severity === 'critical').length,
    high: findings.filter(f => f.severity === 'high').length,
    medium: findings.filter(f => f.severity === 'medium').length,
    low: findings.filter(f => f.severity === 'low').length,
  }

  return (
    <Layout>
      <PageHeader
        title="Security Findings"
        subtitle="Rule-based forensic analysis findings with MITRE ATT&CK mapping"
        badge={{ label: `${findings.length} findings`, color: '#ef4444' }}
        actions={
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <select
              className="input-field"
              style={{ padding: '0.4rem 0.75rem', width: 250, fontSize: '0.8rem', background: '#0f172a' }}
              value={invId}
              onChange={(e) => setInvId(e.target.value)}
            >
              {investigations.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.case_id} — {inv.name}
                </option>
              ))}
            </select>
            <button className="btn-secondary" onClick={() => setFilter('')}><RefreshCw size={14} /></button>
          </div>
        }
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        {/* Summary cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
          {[
            { label: 'Critical', count: counts.critical, color: '#ef4444' },
            { label: 'High', count: counts.high, color: '#f97316' },
            { label: 'Medium', count: counts.medium, color: '#eab308' },
            { label: 'Low', count: counts.low, color: '#22c55e' },
          ].map(item => (
            <div key={item.label} className="glass-card glass-card-hover"
              onClick={() => setFilter(item.label.toLowerCase())}
              style={{
                padding: '1rem', cursor: 'pointer',
                borderTop: `3px solid ${item.color}`,
              }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: item.color }}>{item.count}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{item.label} Severity</div>
            </div>
          ))}
        </div>

        {/* Filter */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', alignItems: 'center' }}>
          <Filter size={14} color="#475569" />
          {['', 'critical', 'high', 'medium', 'low'].map(sev => (
            <button key={sev} onClick={() => setFilter(sev)}
              className={filter === sev ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem' }}>
              {sev || 'All'}
            </button>
          ))}
        </div>

        {/* Findings list */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#475569' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }} />
            Loading findings...
          </div>
        ) : findings.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#475569' }}>
            <Shield size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <p>No findings. Run an investigation to analyze evidence.</p>
          </div>
        ) : (
          findings.map(f => <FindingCard key={f.id} f={f} />)
        )}
      </div>
    </Layout>
  )
}
