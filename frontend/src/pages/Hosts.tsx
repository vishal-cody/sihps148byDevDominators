import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { hostsAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { Monitor, RefreshCw, Search, Wifi, WifiOff } from 'lucide-react'

export default function Hosts() {
  const navigate = useNavigate()
  const [hosts, setHosts] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const r = await hostsAPI.list()
      setHosts(r.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const filtered = hosts.filter(h =>
    h.hostname.toLowerCase().includes(search.toLowerCase()) ||
    (h.ip_address || '').includes(search)
  )

  return (
    <Layout>
      <PageHeader
        title="Host Management"
        subtitle="Monitor and manage all registered forensic endpoints"
        badge={{ label: `${hosts.filter(h => h.status === 'online').length} online`, color: '#10b981' }}
        actions={<button className="btn-secondary" onClick={load}><RefreshCw size={14} /></button>}
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        <div style={{ position: 'relative', maxWidth: 400, marginBottom: '1.25rem' }}>
          <Search size={15} color="#475569" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input className="input-field" style={{ paddingLeft: '2.25rem' }}
            placeholder="Search hosts..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {filtered.map(host => (
            <div key={host.id} className="glass-card glass-card-hover"
              style={{ padding: '1.25rem', cursor: 'pointer' }}
              onClick={() => navigate(`/hosts/${host.id}`)}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8,
                    background: host.os_type === 'windows' ? 'rgba(0,120,212,0.1)' : 'rgba(234,103,54,0.1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem',
                    border: `1px solid ${host.os_type === 'windows' ? 'rgba(0,120,212,0.2)' : 'rgba(234,103,54,0.2)'}`,
                  }}>
                    {host.os_type === 'windows' ? '🪟' : '🐧'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{host.hostname}</div>
                    <div style={{ fontSize: '0.72rem', color: '#475569' }}>{host.ip_address}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  {host.status === 'online' ? <Wifi size={14} color="#10b981" /> : <WifiOff size={14} color="#64748b" />}
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 600,
                    color: host.status === 'online' ? '#10b981' : host.status === 'investigating' ? '#f59e0b' : '#64748b',
                  }}>
                    {host.status}
                  </span>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.75rem' }}>
                <div style={{ color: '#475569' }}>OS: <span style={{ color: '#94a3b8' }}>{host.os_version?.split(' ').slice(0, 3).join(' ')}</span></div>
                <div style={{ color: '#475569' }}>Agent: <span style={{ color: '#94a3b8' }}>v{host.agent_version || '—'}</span></div>
                <div style={{ color: '#475569', gridColumn: 'span 2' }}>
                  Last seen: <span style={{ color: '#94a3b8' }}>
                    {host.last_seen ? new Date(host.last_seen).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
