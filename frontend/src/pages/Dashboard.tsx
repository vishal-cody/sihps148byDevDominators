import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { investigationsAPI, hostsAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import {
  Monitor, Search, AlertTriangle, Shield, Activity,
  TrendingUp, Clock, Server, ChevronRight, RefreshCw
} from 'lucide-react'

interface StatCard {
  label: string
  value: string | number
  sub?: string
  icon: any
  color: string
  trend?: string
}

import { motion } from 'framer-motion'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
}

function StatCard({ label, value, sub, icon: Icon, color, trend }: StatCard) {
  return (
    <motion.div variants={item} className="glass-card glass-card-hover" style={{ 
      padding: '1.5rem', 
      position: 'relative',
      overflow: 'hidden',
      borderTop: `2px solid ${color}40`,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      minHeight: '130px'
    }}>
      {/* Watermark Icon */}
      <div style={{
        position: 'absolute',
        bottom: '-15%',
        right: '-5%',
        opacity: 0.04,
        transform: 'rotate(-15deg)',
        pointerEvents: 'none'
      }}>
        <Icon size={110} color={color} />
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', position: 'relative', zIndex: 1 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6,
          background: `linear-gradient(135deg, ${color}20, ${color}10)`,
          border: `1px solid ${color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 0 10px ${color}20`
        }}>
          <Icon size={14} color={color} />
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {label}
        </p>
      </div>

      <div style={{ position: 'relative', zIndex: 1, marginTop: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
          <p style={{ 
            fontSize: '2.4rem', 
            fontWeight: 800, 
            color: 'var(--color-text-primary)', 
            lineHeight: 1,
            fontFamily: 'JetBrains Mono, monospace',
            letterSpacing: '-0.04em'
          }}>
            {value}
          </p>
          {trend && (
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '0.15rem 0.4rem', borderRadius: 4 }}>
              +{trend}
            </span>
          )}
        </div>
        {sub && <p style={{ fontSize: '0.75rem', color: color, marginTop: '0.4rem', fontWeight: 600 }}>{sub}</p>}
      </div>
    </motion.div>
  )
}

function SeverityBar({ critical, high, medium, low }: any) {
  const total = critical + high + medium + low || 1
  return (
    <div style={{ display: 'flex', height: 6, borderRadius: 3, overflow: 'hidden', gap: 1 }}>
      <div style={{ width: `${(critical/total)*100}%`, background: '#ef4444' }} />
      <div style={{ width: `${(high/total)*100}%`, background: '#f97316' }} />
      <div style={{ width: `${(medium/total)*100}%`, background: '#eab308' }} />
      <div style={{ width: `${(low/total)*100}%`, background: '#22c55e' }} />
    </div>
  )
}



function SeverityBadge({ sev }: { sev: string }) {
  return (
    <span className={`badge-${sev}`} style={{
      padding: '0.15rem 0.5rem', borderRadius: 4,
      fontSize: '0.65rem', fontWeight: 600, textTransform: 'uppercase',
    }}>
      {sev}
    </span>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [hostStats, setHostStats] = useState<any>({ total: 0, online: 0, offline: 0, investigating: 0 })
  const [invStats, setInvStats] = useState<any>({ total_investigations: 0, active_investigations: 0, high_findings: 0, medium_findings: 0, low_findings: 0 })
  const [investigations, setInvestigations] = useState<any[]>([])
  const [hosts, setHosts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [hs, is_, invList, hostList] = await Promise.all([
        hostsAPI.stats(), investigationsAPI.stats(),
        investigationsAPI.list(), hostsAPI.list(),
      ])
      setHostStats(hs.data)
      setInvStats(is_.data)
      setInvestigations(invList.data.slice(0, 6))
      setHosts(hostList.data.slice(0, 8))
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const STAT_CARDS: StatCard[] = [
    { label: 'Total Hosts', value: hostStats.total, sub: `${hostStats.online} online`, icon: Monitor, color: '#3b82f6' },
    { label: 'Online', value: hostStats.online, sub: 'Active agents', icon: Activity, color: '#10b981' },
    { label: 'Investigations', value: invStats.total_investigations, sub: `${invStats.active_investigations} active`, icon: Search, color: '#8b5cf6' },
    { label: 'Critical + High', value: (invStats.high_findings || 0), sub: 'Open findings', icon: AlertTriangle, color: '#ef4444' },
    { label: 'Medium', value: invStats.medium_findings || 0, sub: 'Findings', icon: TrendingUp, color: '#f59e0b' },
    { label: 'Low', value: invStats.low_findings || 0, sub: 'Findings', icon: Shield, color: '#22c55e' },
  ]

  const statusColor: Record<string, string> = {
    online: '#10b981', offline: '#64748b', investigating: '#f59e0b'
  }

  return (
    <Layout>
      <PageHeader
        title="SOC Dashboard"
        subtitle="JOCKY Forensic Investigation Platform — Real-time Overview"
        badge={{ label: 'LIVE', color: '#10b981' }}
        actions={
          <button className="btn-secondary" onClick={load} style={{ gap: '0.4rem' }}>
            <RefreshCw size={14} /> Refresh
          </button>
        }
      />

      <div style={{ padding: '1.5rem 2rem', flex: 1 }}>
        {/* Stat cards */}
        <motion.div 
          variants={container} 
          initial="hidden" 
          animate="show"
          style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}
        >
          {STAT_CARDS.map((c) => <StatCard key={c.label} {...c} />)}
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* Investigations */}
          <div className="glass-card" style={{ overflow: 'hidden' }}>
            <div style={{
              padding: '1rem 1.25rem', borderBottom: '1px solid var(--color-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Search size={15} color="#3b82f6" />
                <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Recent Investigations</span>
              </div>
              <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
                onClick={() => navigate('/investigations')}>
                View all <ChevronRight size={12} />
              </button>
            </div>
            <div>
              {investigations.map((inv) => (
                <div key={inv.id}
                  onClick={() => navigate(`/investigations/${inv.id}`)}
                  style={{
                    padding: '0.875rem 1.25rem', cursor: 'pointer',
                    borderBottom: '1px solid var(--color-border-subtle)',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{inv.name}</span>
                    <SeverityBadge sev={inv.priority} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    <span>{inv.case_id}</span>
                    <span>{inv.host_count} hosts</span>
                    <span style={{ color: inv.high_findings > 0 ? 'var(--color-critical)' : 'var(--color-low)' }}>
                      {inv.high_findings} high findings
                    </span>
                    <span style={{
                      marginLeft: 'auto', padding: '0.1rem 0.5rem', borderRadius: 4,
                      background: inv.status === 'completed' ? 'rgba(16,185,129,0.1)' :
                        inv.status === 'running' ? 'rgba(245,158,11,0.1)' : 'rgba(100,116,139,0.1)',
                      color: inv.status === 'completed' ? '#10b981' :
                        inv.status === 'running' ? '#f59e0b' : '#64748b',
                      fontSize: '0.65rem', fontWeight: 600, textTransform: 'uppercase',
                    }}>
                      {inv.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hosts */}
          <div className="glass-card" style={{ overflow: 'hidden' }}>
            <div style={{
              padding: '1rem 1.25rem', borderBottom: '1px solid var(--color-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Server size={15} color="#3b82f6" />
                <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Host Status</span>
              </div>
              <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
                onClick={() => navigate('/hosts')}>
                Manage hosts <ChevronRight size={12} />
              </button>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Host</th>
                  <th>OS</th>
                  <th>Status</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {hosts.map((h) => (
                  <tr key={h.id} style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/hosts/${h.id}`)}>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--color-text-primary)' }}>{h.hostname}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{h.ip_address}</div>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                      {h.os_type === 'windows' ? '🪟' : '🐧'} {h.os_type}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span className={`status-dot ${h.status}`} />
                        <span style={{ fontSize: '0.75rem', color: statusColor[h.status] || '#64748b' }}>
                          {h.status}
                        </span>
                      </div>
                    </td>
                    <td style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                      {h.last_seen ? new Date(h.last_seen).toLocaleTimeString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Findings bar */}
        <div className="glass-card" style={{ padding: '1.25rem', marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <AlertTriangle size={15} color="#f97316" />
            <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Findings Risk Distribution</span>
          </div>
          <SeverityBar
            critical={Math.floor((invStats.high_findings || 0) * 0.3)}
            high={Math.floor((invStats.high_findings || 0) * 0.7)}
            medium={invStats.medium_findings || 0}
            low={invStats.low_findings || 0}
          />
          <div style={{ display: 'flex', gap: '2rem', marginTop: '0.75rem' }}>
            {[
              { label: 'Critical', color: '#ef4444', val: Math.floor((invStats.high_findings || 0) * 0.3) },
              { label: 'High', color: '#f97316', val: Math.floor((invStats.high_findings || 0) * 0.7) },
              { label: 'Medium', color: '#eab308', val: invStats.medium_findings || 0 },
              { label: 'Low', color: '#22c55e', val: invStats.low_findings || 0 },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: item.color }} />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{item.label}: <strong style={{ color: item.color }}>{item.val}</strong></span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
