import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Investigations from '@/pages/Investigations'
import Hosts from '@/pages/Hosts'
import Timeline from '@/pages/Timeline'
import Findings from '@/pages/Findings'
import Graph from '@/pages/Graph'
import JockyStudio from '@/pages/JockyStudio'
import Reports from '@/pages/Reports'
import Settings from '@/pages/Settings'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div style={{
        height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#0a0e1a', flexDirection: 'column', gap: '1rem',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 12,
          background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'pulse 1.5s infinite',
        }}>⚡</div>
        <p style={{ color: '#475569', fontSize: '0.875rem' }}>Loading JOCKY Platform...</p>
      </div>
    )
  }
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

// Stub pages for routes not yet fully implemented
const StubPage = ({ title }: { title: string }) => {
  const { Layout, PageHeader } = require('@/components/layout/Layout')
  return (
    <Layout>
      <PageHeader title={title} subtitle="Coming soon" />
      <div style={{ padding: '3rem', textAlign: 'center', color: '#475569' }}>
        <p>This view is part of the full JOCKY platform implementation.</p>
      </div>
    </Layout>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/investigations" element={<PrivateRoute><Investigations /></PrivateRoute>} />
          <Route path="/investigations/:id" element={<PrivateRoute><Investigations /></PrivateRoute>} />
          <Route path="/hosts" element={<PrivateRoute><Hosts /></PrivateRoute>} />
          <Route path="/hosts/:id" element={<PrivateRoute><Hosts /></PrivateRoute>} />
          <Route path="/timeline" element={<PrivateRoute><Timeline /></PrivateRoute>} />
          <Route path="/findings" element={<PrivateRoute><Findings /></PrivateRoute>} />
          <Route path="/graph" element={<PrivateRoute><Graph /></PrivateRoute>} />
          <Route path="/jocky" element={<PrivateRoute><JockyStudio /></PrivateRoute>} />
          <Route path="/compiler" element={<PrivateRoute><JockyStudio /></PrivateRoute>} />
          <Route path="/builds" element={<PrivateRoute><JockyStudio /></PrivateRoute>} />
          <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/evidence" element={<PrivateRoute><Timeline /></PrivateRoute>} />
          <Route path="/network" element={<PrivateRoute><Graph /></PrivateRoute>} />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
