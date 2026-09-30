import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { investigationsAPI, hostsAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { Plus, Search, RefreshCw, ChevronRight, Play } from 'lucide-react'

function PriorityBadge({ p }: { p: string }) {
  const colors: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' }
  const c = colors[p] || '#64748b'
  return (
    <span style={{
      padding: '0.15rem 0.5rem', borderRadius: 4,
      fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
      background: `${c}18`, color: c, border: `1px solid ${c}30`,
    }}>{p}</span>
  )
}

function StatusChip({ s }: { s: string }) {
  const m: Record<string, [string, string]> = {
    completed: ['#10b981', 'rgba(16,185,129,0.1)'],
    running: ['#f59e0b', 'rgba(245,158,11,0.1)'],
    created: ['#3b82f6', 'rgba(59,130,246,0.1)'],
    failed: ['#ef4444', 'rgba(239,68,68,0.1)'],
  }
  const [color, bg] = m[s] || ['#64748b', 'rgba(100,116,139,0.1)']
  return (
    <span style={{
      padding: '0.2rem 0.6rem', borderRadius: 100,
      fontSize: '0.7rem', fontWeight: 600, background: bg, color,
      textTransform: 'capitalize',
    }}>{s}</span>
  )
}

export default function Investigations() {
  const navigate = useNavigate()
  const [investigations, setInvestigations] = useState<any[]>([])
  const [hosts, setHosts] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', priority: 'high', assigned_hosts: [] as string[] })
  const [creating, setCreating] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [inv, h] = await Promise.all([investigationsAPI.list(), hostsAPI.list()])
      setInvestigations(inv.data)
      setHosts(h.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const filtered = investigations.filter(i =>
    i.name.toLowerCase().includes(search.toLowerCase()) ||
    i.case_id.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async (e: any) => {
    e.preventDefault()
    setCreating(true)
    try {
      const res = await investigationsAPI.create(form)
      setShowCreate(false)
      setForm({ name: '', description: '', priority: 'high', assigned_hosts: [] })
      navigate(`/investigations/${res.data.id}`)
    } finally { setCreating(false) }
  }

  const handleRun = async (invId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    // Trigger demo mode to automatically simulate endpoint evidence collection and analysis
    await investigationsAPI.run(invId, { mode: 'demo' })
    load()
  }

  return (
    <Layout>
      <PageHeader
        title="Investigations"
        subtitle="Manage and monitor forensic investigations"
        actions={
          <>
            <button className="btn-secondary" onClick={load}><RefreshCw size={14} /></button>
            <button className="btn-primary" onClick={() => setShowCreate(true)}>
              <Plus size={15} /> New Investigation
            </button>
          </>
        }
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        {/* Search */}
        <div style={{ position: 'relative', maxWidth: 400, marginBottom: '1.25rem' }}>
          <Search size={15} color="#475569" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input className="input-field" style={{ paddingLeft: '2.25rem' }}
            placeholder="Search investigations..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        {/* Table */}
        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Name</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Hosts</th>
                <th>High Findings</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(inv => (
                <tr key={inv.id} style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/investigations/${inv.id}`)}>
                  <td><span className="mono" style={{ color: '#3b82f6', fontSize: '0.78rem' }}>{inv.case_id}</span></td>
                  <td><span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{inv.name}</span></td>
                  <td><PriorityBadge p={inv.priority} /></td>
                  <td><StatusChip s={inv.status} /></td>
                  <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{inv.host_count}</td>
                  <td>
                    {inv.high_findings > 0 ? (
                      <span style={{ color: '#ef4444', fontWeight: 700 }}>{inv.high_findings}</span>
                    ) : (
                      <span style={{ color: '#22c55e' }}>0</span>
                    )}
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.75rem' }}>
                    {new Date(inv.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      {inv.status !== 'running' && (
                        <button className="btn-primary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}
                          onClick={e => handleRun(inv.id, e)}>
                          <Play size={11} /> Run
                        </button>
                      )}
                      <button className="btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}>
                        <ChevronRight size={11} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
        }} onClick={() => setShowCreate(false)}>
          <div className="glass-card" style={{ width: 480, padding: '2rem' }}
            onClick={e => e.stopPropagation()}>
            <h2 style={{ fontWeight: 700, marginBottom: '1.5rem' }}>New Investigation</h2>
            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>Name *</label>
                <input className="input-field" value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Q4 Security Sweep" />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>Description</label>
                <textarea className="input-field" value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  rows={3} placeholder="Investigation scope and objectives..." style={{ resize: 'vertical' }} />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>Priority</label>
                <select className="input-field" value={form.priority}
                  onChange={e => setForm({ ...form, priority: e.target.value })}>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>
                  Assign Hosts ({form.assigned_hosts.length} selected)
                </label>
                <div style={{ maxHeight: 150, overflowY: 'auto', border: '1px solid var(--color-border)', borderRadius: 8, padding: '0.5rem' }}>
                  {hosts.map(h => (
                    <label key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem', cursor: 'pointer', fontSize: '0.8rem' }}>
                      <input type="checkbox" checked={form.assigned_hosts.includes(h.id)}
                        onChange={e => setForm({
                          ...form,
                          assigned_hosts: e.target.checked
                            ? [...form.assigned_hosts, h.id]
                            : form.assigned_hosts.filter(id => id !== h.id)
                        })} />
                      <span className={`status-dot ${h.status}`} />
                      {h.hostname} <span style={{ color: '#475569' }}>({h.os_type})</span>
                    </label>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Investigation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
