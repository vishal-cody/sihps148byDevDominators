import React, { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import {
  LayoutDashboard, Search, Monitor, Shield, Clock, GitBranch,
  Code2, Cpu, Package, FileText, Settings, LogOut, Zap,
  Network, AlertTriangle, ChevronRight, Sun, Moon
} from 'lucide-react'

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Investigations', to: '/investigations', icon: Search },
  { label: 'Hosts', to: '/hosts', icon: Monitor },
  { label: 'Evidence', to: '/evidence', icon: Shield, divider: true },
  { label: 'Timeline', to: '/timeline', icon: Clock },
  { label: 'Findings', to: '/findings', icon: AlertTriangle },
  { label: 'Evidence Graph', to: '/graph', icon: GitBranch },
  { label: 'Network', to: '/network', icon: Network, divider: true },
  { label: 'JOCKY Studio', to: '/jocky', icon: Code2 },
  { label: 'Compiler', to: '/compiler', icon: Cpu },
  { label: 'Builds', to: '/builds', icon: Package, divider: true },
  { label: 'Reports', to: '/reports', icon: FileText },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light')
    } else {
      document.documentElement.classList.remove('light')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="flex flex-col h-full" style={{
      width: 280, background: 'var(--color-bg-secondary)',
      borderRight: '1px solid var(--color-border)', flexShrink: 0,
      backdropFilter: 'blur(10px)',
      position: 'relative',
      zIndex: 10
    }}>
      {/* Logo */}
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <div style={{
            width: 44, height: 44, background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
            borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(59,130,246,0.3)',
            flexShrink: 0
          }}>
            <Shield size={24} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 900, fontSize: '1.4rem', letterSpacing: '-0.03em', lineHeight: 1.1 }}
                 className="gradient-text">JOCKY</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginTop: '0.2rem' }}>
              Forensic Platform
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '1rem 0.75rem' }}>
        {NAV_ITEMS.map((item) => (
          <React.Fragment key={item.to}>
            {item.divider && (
              <div style={{ height: 1, background: 'var(--color-border-subtle)', margin: '0.75rem 0.5rem' }} />
            )}
            <NavLink
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              {({ isActive }) => (
                <>
                  <item.icon size={18} />
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {isActive && <ChevronRight size={14} />}
                </>
              )}
            </NavLink>
          </React.Fragment>
        ))}
      </nav>

      {/* User */}
      <div style={{ padding: '0.75rem', borderTop: '1px solid var(--color-border)' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.6rem',
          padding: '0.6rem', borderRadius: 8,
          background: 'var(--color-bg-card)',
        }}>
          <div style={{
            width: 30, height: 30, borderRadius: '50%',
            background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.75rem', fontWeight: 700, color: 'white',
          }}>
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, truncate: 'ellipsis' }}>{user?.username}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>{user?.role}</div>
          </div>
          <button onClick={toggleTheme} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-text-secondary)', padding: '0.25rem', borderRadius: 4,
            transition: 'color 0.15s',
          }}
            title="Toggle Light/Dark Theme"
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-accent)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-secondary)')}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          <button onClick={handleLogout} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-text-secondary)', padding: '0.25rem', borderRadius: 4,
            transition: 'color 0.15s',
          }}
            title="Logout"
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-critical)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-secondary)')}
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  )
}
