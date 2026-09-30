import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Zap, Shield, Eye, EyeOff, Lock, User } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(username, password)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#0a0e1a', padding: '2rem',
    }} className="bg-grid">
      {/* Background glow */}
      <div style={{
        position: 'fixed', top: '20%', left: '50%', transform: 'translateX(-50%)',
        width: 600, height: 300, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(59,130,246,0.08) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div className="glass-card fade-in" style={{ width: '100%', maxWidth: 420, padding: '2.5rem' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: 64, height: 64,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            borderRadius: 16, margin: '0 auto 1rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 30px rgba(59,130,246,0.3)',
          }}>
            <Zap size={32} color="white" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }} className="gradient-text">JOCKY</h1>
          <p style={{ fontSize: '0.8rem', color: '#475569', marginTop: '0.25rem', letterSpacing: '0.1em' }}>
            JOINT CYBER OPERATIONS & KNOWLEDGE YIELDER
          </p>
        </div>

        {/* Info badge */}
        <div style={{
          background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1.5rem',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <Shield size={14} color="#3b82f6" />
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Forensic Investigation Platform — SIH 2025
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Username */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>
              Username
            </label>
            <div style={{ position: 'relative' }}>
              <User size={15} color="#475569" style={{
                position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)'
              }} />
              <input
                type="text" value={username}
                onChange={e => setUsername(e.target.value)}
                className="input-field"
                style={{ paddingLeft: '2.25rem' }}
                placeholder="Username"
              />
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={15} color="#475569" style={{
                position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)'
              }} />
              <input
                type={showPass ? 'text' : 'password'} value={password}
                onChange={e => setPassword(e.target.value)}
                className="input-field"
                style={{ paddingLeft: '2.25rem', paddingRight: '2.5rem' }}
                placeholder="Password"
              />
              <button type="button"
                onClick={() => setShowPass(!showPass)}
                style={{
                  position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: '#475569',
                }}
              >
                {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8, padding: '0.75rem', marginBottom: '1rem',
              fontSize: '0.8rem', color: '#ef4444',
            }}>
              {error}
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}>
            {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : null}
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        {/* Demo creds */}
        <div style={{
          marginTop: '1.5rem', padding: '1rem',
          background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.15)',
          borderRadius: 8,
        }}>
          <p style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600, marginBottom: '0.4rem' }}>
            Demo Credentials
          </p>
          <div style={{ fontSize: '0.72rem', color: '#475569', lineHeight: 1.6 }}>
            Admin: <span className="mono" style={{ color: '#94a3b8' }}>admin / admin123</span><br />
            Investigator: <span className="mono" style={{ color: '#94a3b8' }}>investigator / inv123</span>
          </div>
        </div>
      </div>
    </div>
  )
}
