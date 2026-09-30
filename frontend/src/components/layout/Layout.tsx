import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

import { motion, AnimatePresence } from 'framer-motion'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="ambient-bg">
        <div className="ambient-orb orb-1"></div>
        <div className="ambient-orb orb-2"></div>
        <div className="ambient-orb orb-3"></div>
      </div>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }} className="bg-grid">
        <Sidebar />
        <main style={{
          flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column',
          background: 'transparent', // Let ambient background shine through
        }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </>
  )
}

export function PageHeader({
  title, subtitle, actions, badge
}: {
  title: string
  subtitle?: string
  actions?: ReactNode
  badge?: { label: string; color?: string }
}) {
  return (
    <div style={{
      padding: '1.5rem 2rem',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'var(--color-bg-card)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      position: 'sticky', top: 0, zIndex: 10,
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{title}</h1>
          {badge && (
            <span style={{
              padding: '0.2rem 0.6rem', borderRadius: 100,
              fontSize: '0.7rem', fontWeight: 600,
              background: badge.color ? `${badge.color}20` : 'rgba(59,130,246,0.15)',
              color: badge.color || '#3b82f6',
              border: `1px solid ${badge.color || '#3b82f6'}40`,
            }}>
              {badge.label}
            </span>
          )}
        </div>
        {subtitle && (
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>{actions}</div>}
    </div>
  )
}
