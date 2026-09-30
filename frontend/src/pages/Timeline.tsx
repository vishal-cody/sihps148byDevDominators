import { useEffect, useState } from 'react'
import { evidenceAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { Clock, Filter, AlertTriangle, RefreshCw } from 'lucide-react'

function SeverityDot({ sev }: { sev: string }) {
  const colors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', warning: '#eab308', info: '#3b82f6', low: '#22c55e'
  }
  return (
    <div style={{
      width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
      background: colors[sev] || '#475569',
      boxShadow: ['critical', 'high'].includes(sev) ? `0 0 6px ${colors[sev]}` : 'none',
    }} />
  )
}

function EventTypeBadge({ type }: { type: string }) {
  const icons: Record<string, string> = {
    process_start: '⚙', process_stop: '⛔', network_connect: '🌐',
    network_disconnect: '🔌', persistence_created: '🔒', file_created: '📄',
    file_modified: '✏', authentication: '🔑', system_event: '🖥', registry_modification: '🗝',
  }
  return (
    <span style={{
      padding: '0.1rem 0.4rem', borderRadius: 4, fontSize: '0.65rem',
      background: 'rgba(59,130,246,0.08)', color: '#64748b',
      fontFamily: 'JetBrains Mono, monospace',
    }}>
      {icons[type] || '•'} {type?.replace(/_/g, ' ')}
    </span>
  )
}

const DEMO_INV_ID_KEY = 'jocky_demo_inv_id'

export default function Timeline() {
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ severity: '', event_type: '', suspicious_only: false })
  const [invId, setInvId] = useState('')

  useEffect(() => {
    // Try to get demo investigation ID from localStorage or fetch it
    const stored = localStorage.getItem(DEMO_INV_ID_KEY)
    if (stored) { setInvId(stored); return }
    // Fetch from investigations
    import('@/services/api').then(({ investigationsAPI }) => {
      investigationsAPI.list().then(r => {
        if (r.data.length > 0) {
          const id = r.data[0].id
          setInvId(id)
          localStorage.setItem(DEMO_INV_ID_KEY, id)
        }
      })
    })
  }, [])

  useEffect(() => {
    if (!invId) return
    const load = async () => {
      setLoading(true)
      try {
        const params: any = { limit: 300 }
        if (filter.severity) params.severity = filter.severity
        if (filter.event_type) params.event_type = filter.event_type
        const r = await evidenceAPI.timeline(invId, params)
        let data = r.data
        if (filter.suspicious_only) data = data.filter((e: any) => e.is_suspicious)
        setEvents(data)
      } finally { setLoading(false) }
    }
    load()
  }, [invId, filter])

  const suspCount = events.filter(e => e.is_suspicious).length

  return (
    <Layout>
      <PageHeader
        title="Investigation Timeline"
        subtitle="Chronological forensic event stream across all hosts"
        badge={{ label: `${events.length} events`, color: '#3b82f6' }}
        actions={
          <button className="btn-secondary" onClick={() => setFilter({ severity: '', event_type: '', suspicious_only: false })}>
            <RefreshCw size={14} /> Reset Filters
          </button>
        }
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        {/* Filters */}
        <div className="glass-card" style={{ padding: '1rem', marginBottom: '1.25rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <Filter size={15} color="#475569" />
          <select className="input-field" style={{ width: 160 }} value={filter.severity}
            onChange={e => setFilter({ ...filter, severity: e.target.value })}>
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          <select className="input-field" style={{ width: 200 }} value={filter.event_type}
            onChange={e => setFilter({ ...filter, event_type: e.target.value })}>
            <option value="">All Event Types</option>
            <option value="process_start">Process Start</option>
            <option value="network_connect">Network Connect</option>
            <option value="persistence_created">Persistence Created</option>
            <option value="authentication">Authentication</option>
            <option value="system_event">System Event</option>
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={filter.suspicious_only}
              onChange={e => setFilter({ ...filter, suspicious_only: e.target.checked })} />
            <AlertTriangle size={13} color="#f97316" /> Suspicious only ({suspCount})
          </label>
        </div>

        {/* Timeline */}
        <div className="glass-card" style={{ padding: '1.5rem', maxHeight: 'calc(100vh - 260px)', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }} />
              Loading timeline...
            </div>
          ) : events.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#475569' }}>
              <Clock size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
              <p>No events found. Run an investigation first.</p>
            </div>
          ) : (
            <div style={{ paddingLeft: '0.5rem' }}>
              {events.map((evt, i) => (
                <div key={evt.id || i}
                  className={`timeline-item ${evt.is_suspicious ? 'suspicious' : evt.severity}`}
                  style={{ paddingBottom: '1rem' }}>
                  <div style={{ minWidth: 90, fontSize: '0.7rem', color: '#475569', fontFamily: 'monospace', paddingTop: '0.1rem' }}>
                    {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '—'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.2rem' }}>
                      <SeverityDot sev={evt.severity} />
                      <span style={{
                        fontWeight: 600, fontSize: '0.82rem',
                        color: evt.is_suspicious ? '#ef4444' : '#e2e8f0',
                      }}>
                        {evt.title}
                      </span>
                      <EventTypeBadge type={evt.event_type} />
                      {evt.is_suspicious && (
                        <span style={{
                          padding: '0.1rem 0.4rem', borderRadius: 4,
                          background: 'rgba(239,68,68,0.15)', color: '#ef4444',
                          fontSize: '0.6rem', fontWeight: 700, textTransform: 'uppercase',
                        }}>⚠ Suspicious</span>
                      )}
                    </div>
                    {evt.description && (
                      <p style={{ fontSize: '0.75rem', color: '#64748b', lineHeight: 1.4 }}>{evt.description}</p>
                    )}
                    {(evt.actor || evt.target) && (
                      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.25rem' }}>
                        {evt.actor && <span style={{ fontSize: '0.7rem', color: '#475569' }}>Actor: <strong style={{ color: '#94a3b8' }}>{evt.actor}</strong></span>}
                        {evt.target && <span style={{ fontSize: '0.7rem', color: '#475569' }}>Target: <strong style={{ color: '#94a3b8' }}>{evt.target}</strong></span>}
                        <span style={{ fontSize: '0.7rem', color: '#475569', marginLeft: 'auto' }}>
                          Host: <strong style={{ color: '#3b82f6' }}>{evt.host_id?.substring(0, 8)}...</strong>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
