import { useState } from 'react'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { Shield, AlertTriangle, CheckCircle2, XCircle, Cpu, ArrowRight } from 'lucide-react'

const SCENARIOS = [
  {
    id: 'edr',
    name: 'EDR Interference Simulation',
    description: 'Demonstrates how traditional forensic tools are blocked by behavioral EDR while JOCKY abstracted execution proceeds.',
    traditional: {
      tool: 'Traditional PowerShell Forensic Script',
      detections: [
        { type: 'Behavioral Heuristic', msg: 'Suspicious PowerShell enumeration pattern', blocked: true },
        { type: 'Memory Scanning', msg: 'Known forensic tool signature in memory', blocked: true },
        { type: 'File Reputation', msg: 'Script hash not in allowlist', blocked: true },
        { type: 'Kernel Telemetry', msg: 'ETW provider hooks detected', blocked: true },
      ]
    },
    jocky: {
      tool: 'JOCKY Forensic IR Job',
      detections: [
        { type: 'Behavioral Heuristic', msg: 'JOCKY IR execution — abstracted from direct API calls', allowed: true },
        { type: 'Memory Scanning', msg: 'Polymorphic build variant — no static signature match', allowed: true },
        { type: 'File Reputation', msg: 'JOCKY build hash varies per profile (diversified build)', allowed: true },
        { type: 'Kernel Telemetry', msg: 'No direct kernel hooks — user-mode abstraction layer', allowed: true },
      ]
    }
  },
  {
    id: 'signature',
    name: 'Signature Detection Evasion Simulation',
    description: 'Shows how JOCKY IR transformation produces builds with different hashes while forensic functionality remains identical.',
    traditional: {
      tool: 'Static Forensic Binary',
      detections: [
        { type: 'Hash Signature', msg: 'SHA-256 matches threat actor forensic tool IOC', blocked: true },
        { type: 'String Detection', msg: 'Known forensic strings in binary', blocked: true },
      ]
    },
    jocky: {
      tool: 'JOCKY Variant Build',
      detections: [
        { type: 'Hash Signature', msg: 'Build A SHA: a3f2... | Build B SHA: d9c1... — different hashes, same output', allowed: true },
        { type: 'String Detection', msg: 'Identifier renaming: collect_processes → ENUM_PROC_01 (per build)', allowed: true },
      ]
    }
  }
]

export default function Settings() {
  const [activeScenario, setActiveScenario] = useState(SCENARIOS[0])
  const [running, setRunning] = useState(false)
  const [revealed, setRevealed] = useState(false)

  const runSim = () => {
    setRunning(true)
    setRevealed(false)
    setTimeout(() => { setRunning(false); setRevealed(true) }, 2000)
  }

  return (
    <Layout>
      <PageHeader
        title="Security Resilience Lab"
        subtitle="Controlled simulation of forensic tool compatibility scenarios"
        badge={{ label: 'SIMULATION ONLY', color: '#f59e0b' }}
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        {/* Disclaimer */}
        <div style={{
          padding: '1rem 1.25rem', borderRadius: 10, marginBottom: '1.5rem',
          background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
          display: 'flex', gap: '0.75rem',
        }}>
          <AlertTriangle size={20} color="#f59e0b" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <p style={{ fontWeight: 700, color: '#f59e0b', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
              Controlled Simulation — No Real Security Control Bypass Is Performed
            </p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5 }}>
              All scenarios below are simulated demonstrations of forensic tool compatibility challenges.
              JOCKY Platform does not implement EDR disabling, antivirus bypass, kernel manipulation,
              credential theft, or any form of real security product tampering. The IR transformation
              engine uses only safe, semantic-preserving code transformations.
            </p>
          </div>
        </div>

        {/* Scenario picker */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {SCENARIOS.map(s => (
            <button key={s.id} onClick={() => { setActiveScenario(s); setRevealed(false) }}
              className={activeScenario.id === s.id ? 'btn-primary' : 'btn-secondary'}
              style={{ fontSize: '0.8rem' }}>
              {s.name}
            </button>
          ))}
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>{activeScenario.name}</h3>
          <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1.25rem' }}>{activeScenario.description}</p>

          <button className="btn-primary" onClick={runSim} disabled={running}
            style={{ marginBottom: '1.5rem' }}>
            {running ? (
              <><span className="spinner" style={{ width: 16, height: 16 }} /> Running Simulation...</>
            ) : (
              <><Cpu size={15} /> Run Simulation</>
            )}
          </button>

          {(revealed || !running) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1.5rem', alignItems: 'start' }}>
              {/* Traditional tool */}
              <div>
                <div style={{
                  padding: '0.75rem 1rem', borderRadius: '8px 8px 0 0',
                  background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                  borderBottom: 'none',
                }}>
                  <div style={{ fontSize: '0.7rem', color: '#ef4444', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    Traditional Tool
                  </div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{activeScenario.traditional.tool}</div>
                </div>
                <div style={{ border: '1px solid rgba(239,68,68,0.2)', borderRadius: '0 0 8px 8px', overflow: 'hidden' }}>
                  {activeScenario.traditional.detections.map((d, i) => (
                    <div key={i} style={{
                      padding: '0.6rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                      background: 'rgba(239,68,68,0.03)', borderBottom: i < activeScenario.traditional.detections.length - 1 ? '1px solid rgba(239,68,68,0.1)' : 'none',
                    }}>
                      <XCircle size={13} color="#ef4444" style={{ flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#ef4444' }}>{d.type}</div>
                        <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{d.msg}</div>
                      </div>
                    </div>
                  ))}
                  <div style={{ padding: '0.75rem', textAlign: 'center', background: 'rgba(239,68,68,0.1)', borderTop: '1px solid rgba(239,68,68,0.2)' }}>
                    <span style={{ color: '#ef4444', fontWeight: 800, fontSize: '0.9rem' }}>⛔ BLOCKED</span>
                  </div>
                </div>
              </div>

              {/* Arrow */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '3rem', gap: '0.5rem', color: '#475569', fontSize: '0.7rem' }}>
                <ArrowRight size={20} />
                <span>vs</span>
              </div>

              {/* JOCKY */}
              <div>
                <div style={{
                  padding: '0.75rem 1rem', borderRadius: '8px 8px 0 0',
                  background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                  borderBottom: 'none',
                }}>
                  <div style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    JOCKY Forensic Job
                  </div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{activeScenario.jocky.tool}</div>
                </div>
                <div style={{ border: '1px solid rgba(16,185,129,0.2)', borderRadius: '0 0 8px 8px', overflow: 'hidden' }}>
                  {activeScenario.jocky.detections.map((d: any, i) => (
                    <div key={i} style={{
                      padding: '0.6rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                      background: 'rgba(16,185,129,0.03)', borderBottom: i < activeScenario.jocky.detections.length - 1 ? '1px solid rgba(16,185,129,0.1)' : 'none',
                    }}>
                      <CheckCircle2 size={13} color="#10b981" style={{ flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#10b981' }}>{d.type}</div>
                        <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{d.msg}</div>
                      </div>
                    </div>
                  ))}
                  <div style={{ padding: '0.75rem', textAlign: 'center', background: 'rgba(16,185,129,0.1)', borderTop: '1px solid rgba(16,185,129,0.2)' }}>
                    <span style={{ color: '#10b981', fontWeight: 800, fontSize: '0.9rem' }}>✅ ALLOWED</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
