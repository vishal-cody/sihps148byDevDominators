import { useState, useRef, useEffect } from 'react'
import { jockyAPI, investigationsAPI } from '@/services/api'
import { Layout, PageHeader } from '@/components/layout/Layout'
import {
  CheckCircle2, XCircle, Loader2, Play, Cpu, Package,
  GitBranch, Rocket, Save, ChevronRight, Code2, FileText, Hash, Plus
} from 'lucide-react'
import Editor from '@monaco-editor/react'

const DEFAULT_SCRIPT = `investigation "Enterprise Security Sweep" {
    // Collect forensic evidence from all targets
    collect system_info
    collect processes
    collect network_connections
    collect persistence
    collect event_logs
    collect filesystem

    // Analyze collected data
    analyze processes
    analyze network_connections

    // Apply filters
    filter processes where cpu > 10
    filter network_connections where port in [4444, 1337, 8080]

    // Generate outputs
    generate timeline
    generate report
}`

const SAMPLE_SCRIPTS = [
  { name: 'Enterprise Sweep', code: DEFAULT_SCRIPT },
  {
    name: 'Quick Process Scan', code: `host "HOST-001" {
    collect processes
    collect network_connections
    filter processes where cpu > 50
    analyze processes
    generate report
}`
  },
  {
    name: 'Persistence Audit', code: `investigation "Persistence Audit" {
    collect persistence
    collect event_logs
    analyze persistence
    generate timeline
    generate report
}`
  },
]

function StepIndicator({ steps, loading }: any) {
  return (
    <div style={{ padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      {steps.map((step: any, i: number) => (
        <div key={i} className={`compiler-step ${step.status}`}>
          {step.status === 'ok' && <CheckCircle2 size={13} color="#10b981" />}
          {step.status === 'error' && <XCircle size={13} color="#ef4444" />}
          {step.status === 'pending' && (loading ? <Loader2 size={13} className="animate-spin" /> : <div style={{ width: 13, height: 13, borderRadius: '50%', border: '1px solid #475569' }} />)}
          <span style={{ flex: 1 }}>{step.step}</span>
          {step.detail && <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>{step.detail}</span>}
        </div>
      ))}
    </div>
  )
}

function BuildCard({ build, label }: any) {
  if (!build) return null
  return (
    <div style={{
      background: 'rgba(19,25,41,0.8)', border: '1px solid #1e2d4a',
      borderRadius: 8, padding: '1rem',
    }}>
      <div style={{ fontSize: '0.7rem', color: '#475569', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
        <Hash size={12} color="#94a3b8" />
        <span className="mono" style={{ fontSize: '0.65rem', color: '#94a3b8', wordBreak: 'break-all' }}>
          {build.sha256?.substring(0, 32)}...
        </span>
      </div>
      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
        Profile: <span style={{ color: '#3b82f6' }}>{build.profile}</span>
      </div>
      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
        IR Nodes: <span style={{ color: '#e2e8f0' }}>{build.ir_node_count}</span>
      </div>
    </div>
  )
}

export default function JockyStudio() {
  const [code, setCode] = useState(() => sessionStorage.getItem('jocky_studio_code') || DEFAULT_SCRIPT)
  const [validateResult, setValidateResult] = useState<any>(() => JSON.parse(sessionStorage.getItem('jocky_studio_val') || 'null'))
  const [compileResult, setCompileResult] = useState<any>(() => JSON.parse(sessionStorage.getItem('jocky_studio_comp') || 'null'))
  const [buildResult, setBuildResult] = useState<any>(() => JSON.parse(sessionStorage.getItem('jocky_studio_bld') || 'null'))
  const [variantResult, setVariantResult] = useState<any>(() => JSON.parse(sessionStorage.getItem('jocky_studio_var') || 'null'))
  const [loading, setLoading] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'output' | 'ir' | 'builds'>(() => (sessionStorage.getItem('jocky_studio_tab') as any) || 'output')
  const [selectedFile, setSelectedFile] = useState(0)
  const [scripts, setScripts] = useState<any[]>([...SAMPLE_SCRIPTS])
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [saveName, setSaveName] = useState('My Script')

  const loadScripts = async () => {
    try {
      const res = await jockyAPI.listScripts()
      const dbScripts = res.data.map((s: any) => ({ name: s.name, code: s.source_code }))
      setScripts([...SAMPLE_SCRIPTS, ...dbScripts])
    } catch (e) {
      console.error('Failed to load scripts', e)
    }
  }

  useEffect(() => {
    loadScripts()
  }, [])

  useEffect(() => {
    sessionStorage.setItem('jocky_studio_code', code)
    sessionStorage.setItem('jocky_studio_val', JSON.stringify(validateResult))
    sessionStorage.setItem('jocky_studio_comp', JSON.stringify(compileResult))
    sessionStorage.setItem('jocky_studio_bld', JSON.stringify(buildResult))
    sessionStorage.setItem('jocky_studio_var', JSON.stringify(variantResult))
    sessionStorage.setItem('jocky_studio_tab', activeTab)
  }, [code, validateResult, compileResult, buildResult, variantResult, activeTab])

  const PIPELINE_STEPS = [
    { step: 'Lexer', status: validateResult ? (validateResult.steps?.[0]?.status || 'pending') : 'pending',
      detail: validateResult?.steps?.[0]?.detail },
    { step: 'Parser', status: validateResult ? (validateResult.steps?.[1]?.status || 'pending') : 'pending',
      detail: validateResult?.steps?.[1]?.detail },
    { step: 'AST', status: validateResult?.valid ? 'ok' : (validateResult ? 'error' : 'pending'), detail: null },
    { step: 'Semantic Analysis', status: validateResult ? (validateResult.steps?.[2]?.status || 'pending') : 'pending',
      detail: validateResult?.steps?.[2]?.detail },
    { step: 'JOCKY IR', status: compileResult?.success ? 'ok' : (compileResult ? 'error' : 'pending'),
      detail: compileResult?.steps?.[3]?.detail },
    { step: 'Build', status: buildResult ? 'ok' : 'pending', detail: buildResult ? `SHA-256: ${buildResult.sha256?.substring(0, 16)}...` : null },
  ]

  const doValidate = async () => {
    setLoading('validate')
    try {
      const r = await jockyAPI.validate(code)
      setValidateResult(r.data)
    } finally { setLoading(null) }
  }

  const doCompile = async () => {
    setLoading('compile')
    try {
      const v = await jockyAPI.validate(code)
      setValidateResult(v.data)
      if (!v.data.valid) return
      const c = await jockyAPI.compile(code)
      setCompileResult(c.data)
      setActiveTab('ir')
    } finally { setLoading(null) }
  }

  const doBuild = async () => {
    setLoading('build')
    try {
      const v = await jockyAPI.validate(code)
      setValidateResult(v.data)
      if (!v.data.valid) return
      const c = await jockyAPI.compile(code)
      setCompileResult(c.data)
      const b = await jockyAPI.build(code, 'forensic_standard')
      setBuildResult(b.data)
      setActiveTab('builds')
    } finally { setLoading(null) }
  }

  const doVariant = async () => {
    if (!buildResult?.build_id) { await doBuild(); return }
    setLoading('variant')
    try {
      const r = await jockyAPI.buildVariant(buildResult.build_id)
      setVariantResult(r.data)
      setActiveTab('builds')
    } finally { setLoading(null) }
  }

  const doSave = async () => {
    if (!saveName) return
    setSaveModalOpen(false)
    setLoading('save')
    try {
      await jockyAPI.saveScript({ name: saveName, source_code: code })
      await loadScripts()
      setSelectedFile(SAMPLE_SCRIPTS.length)
      alert('Script saved successfully!')
    } catch (e: any) {
      alert('Save failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(null)
    }
  }

  const doDeploy = async () => {
    if (!buildResult) return
    setLoading('deploy')
    try {
      const name = prompt('Deploy Investigation Name:', 'Studio Deployment - ' + new Date().toLocaleTimeString())
      if (!name) return
      
      // Auto-assign all available hosts to the deployment
      const { hostsAPI } = await import('@/services/api')
      const hRes = await hostsAPI.list()
      const host_ids = hRes.data.map((h: any) => h.id)
      
      const inv = await investigationsAPI.create({
        name,
        description: 'Deployed directly from JOCKY Studio',
        jocky_script_id: buildResult.script_id,
        assigned_hosts: host_ids, // Now the investigation actually has targets!
      })
      alert(`Successfully deployed to investigation: ${inv.data.case_id} targeting ${host_ids.length} hosts.`)
      // Clear state after deploy so next visit is fresh, or keep it
    } catch (e: any) {
      alert('Deploy failed: ' + e.message)
    } finally {
      setLoading(null)
    }
  }

  const doNewScript = () => {
    setCode('')
    setSelectedFile(-1)
    setValidateResult(null)
    setCompileResult(null)
    setBuildResult(null)
    setVariantResult(null)
    setActiveTab('output')
  }

  return (
    <Layout>
      <PageHeader
        title="JOCKY Studio"
        subtitle="Write, compile, and deploy JOCKY forensic investigation scripts"
        badge={{ label: 'IDE', color: '#8b5cf6' }}
        actions={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn-secondary" onClick={() => setSaveModalOpen(true)} disabled={!!loading}>
              {loading === 'save' ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save
            </button>
            <button className="btn-secondary" onClick={doValidate} disabled={!!loading}>
              {loading === 'validate' ? <Loader2 size={14} /> : <CheckCircle2 size={14} />} Validate
            </button>
            <button className="btn-secondary" onClick={doCompile} disabled={!!loading}>
              {loading === 'compile' ? <Loader2 size={14} /> : <Cpu size={14} />} Compile
            </button>
            <button className="btn-secondary" onClick={doBuild} disabled={!!loading}>
              {loading === 'build' ? <Loader2 size={14} /> : <Package size={14} />} Build
            </button>
            <button className="btn-secondary" onClick={doVariant} disabled={!!loading}>
              {loading === 'variant' ? <Loader2 size={14} /> : <GitBranch size={14} />} Variant
            </button>
            <button className="btn-primary" disabled={!buildResult || !!loading} onClick={doDeploy}>
              {loading === 'deploy' ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />} Deploy
            </button>
          </div>
        }
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* File tree */}
        <div style={{
          width: 240, background: 'var(--color-bg-secondary)', borderRight: '1px solid var(--color-border)',
          padding: '1rem 0.75rem', flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 0.5rem', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Files
            </div>
            <button onClick={doNewScript} style={{ background: 'none', border: 'none', color: 'var(--color-accent)', cursor: 'pointer', display: 'flex', alignItems: 'center', transition: 'all 0.15s' }} title="New Script" onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'} onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}>
              <Plus size={16} />
            </button>
          </div>
          {scripts.map((s, i) => (
            <div key={i} onClick={() => { 
              setSelectedFile(i); 
              setCode(s.code);
              setValidateResult(null);
              setCompileResult(null);
              setBuildResult(null);
              setVariantResult(null);
            }}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.6rem 0.75rem', borderRadius: 8, cursor: 'pointer',
                fontSize: '0.85rem', transition: 'all 0.2s', fontWeight: 500,
                color: selectedFile === i ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                background: selectedFile === i ? 'var(--color-accent-glow)' : 'transparent',
                border: selectedFile === i ? '1px solid var(--color-border)' : '1px solid transparent',
                marginBottom: '0.25rem'
              }}
              onMouseEnter={e => {
                if (selectedFile !== i) e.currentTarget.style.background = 'var(--color-bg-hover)'
              }}
              onMouseLeave={e => {
                if (selectedFile !== i) e.currentTarget.style.background = 'transparent'
              }}
            >
              <FileText size={14} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {s.name.toLowerCase().replace(/ /g, '_')}.jky
              </span>
            </div>
          ))}
        </div>

        {/* Editor */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Editor
            height="100%"
            defaultLanguage="javascript"
            theme="vs-dark"
            value={code}
            onChange={(v) => {
              setCode(v || '')
              setBuildResult(null) // Require rebuild on edit
            }}
            onMount={(editor, monaco) => {
              monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
                noSemanticValidation: true,
                noSyntaxValidation: true,
              })
            }}
            options={{
              fontSize: 14, fontFamily: 'JetBrains Mono, monospace',
              minimap: { enabled: false },
              lineNumbers: 'on', wordWrap: 'on',
              scrollBeyondLastLine: false,
              renderLineHighlight: 'gutter',
              padding: { top: 16 },
            }}
          />
        </div>

        {/* Right panel */}
        <div style={{
          width: 380, borderLeft: '1px solid var(--color-border)', display: 'flex',
          flexDirection: 'column', background: 'var(--color-bg-secondary)',
        }}>
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)' }}>
            {(['output', 'ir', 'builds'] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1, padding: '0.8rem 0.6rem', fontSize: '0.75rem', fontWeight: 600,
                  textTransform: 'uppercase', letterSpacing: '0.05em',
                  background: activeTab === tab ? 'var(--color-accent-glow)' : 'transparent', border: 'none', cursor: 'pointer',
                  color: activeTab === tab ? 'var(--color-accent)' : 'var(--color-text-muted)',
                  borderBottom: activeTab === tab ? '2px solid var(--color-accent)' : '2px solid transparent',
                  transition: 'all 0.15s',
                }}>
                {tab === 'output' ? 'Compiler' : tab === 'ir' ? 'IR Viewer' : 'Builds'}
              </button>
            ))}
          </div>

          {/* Panel content */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {activeTab === 'output' && (
              <div>
                {/* Pipeline steps */}
                <div style={{ padding: '1rem', borderBottom: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                    Compiler Pipeline
                  </div>
                  <StepIndicator steps={PIPELINE_STEPS} loading={!!loading} />
                </div>

                {/* Errors/Warnings */}
                {(validateResult?.errors?.length > 0 || compileResult?.errors?.length > 0) && (
                  <div style={{ padding: '1rem', borderBottom: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-critical)', fontWeight: 700, marginBottom: '0.5rem' }}>
                      Errors
                    </div>
                    {[...(validateResult?.errors || []), ...(compileResult?.errors || [])].map((e: string, i: number) => (
                      <div key={i} className="mono" style={{ fontSize: '0.75rem', color: 'var(--color-critical)', marginBottom: '0.25rem' }}>
                        {e}
                      </div>
                    ))}
                  </div>
                )}

                {validateResult?.warnings?.length > 0 && (
                  <div style={{ padding: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-warning)', fontWeight: 700, marginBottom: '0.5rem' }}>
                      Warnings
                    </div>
                    {validateResult.warnings.map((w: string, i: number) => (
                      <div key={i} className="mono" style={{ fontSize: '0.75rem', color: 'var(--color-warning)', marginBottom: '0.25rem' }}>
                        ⚠ {w}
                      </div>
                    ))}
                  </div>
                )}

                {validateResult?.valid && !validateResult?.errors?.length && (
                  <div style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-low)', fontSize: '0.85rem' }}>
                      <CheckCircle2 size={16} /> Script valid — ready to compile
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'ir' && compileResult?.ir && (
              <div style={{ padding: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                  JOCKY IR — {compileResult.ir_node_count} nodes
                </div>
                <pre className="mono" style={{
                  fontSize: '0.75rem', color: 'var(--color-text-secondary)', lineHeight: 1.6,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                  background: 'var(--color-bg-primary)', padding: '1rem', borderRadius: 8,
                  border: '1px solid var(--color-border)'
                }}>
                  {JSON.stringify(compileResult.ir, null, 2)}
                </pre>
              </div>
            )}

            {activeTab === 'builds' && (
              <div style={{ padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {buildResult && (
                  <>
                    <BuildCard build={buildResult} label="Build A — forensic_standard" />
                    {variantResult?.variant && (
                      <BuildCard build={variantResult.variant} label="Build B — forensic_variant" />
                    )}
                    {variantResult && (
                      <div style={{
                        padding: '0.75rem', borderRadius: 8,
                        background: 'rgba(16,185,129,0.08)',
                        border: '1px solid rgba(16,185,129,0.2)',
                      }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                          Functional Equivalence
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <CheckCircle2 size={16} color="var(--color-low)" />
                          <span style={{ color: 'var(--color-low)', fontWeight: 700 }}>IDENTICAL</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '0.4rem' }}>
                          Both builds produce identical forensic output despite different internal representations.
                        </div>
                      </div>
                    )}
                  </>
                )}
                {!buildResult && (
                  <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', textAlign: 'center', padding: '2rem' }}>
                    Click <strong>Build</strong> to generate a compiled artifact
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Save Modal */}
      {saveModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999
        }}>
          <div className="glass-card" style={{
            padding: '2rem', width: 450
          }}>
            <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem', color: 'var(--color-text-primary)' }}>Save Script</h3>
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>Script Name</label>
              <input 
                type="text" 
                value={saveName} 
                onChange={e => setSaveName(e.target.value)}
                className="input-field" 
                style={{ width: '100%' }}
                autoFocus
                onKeyDown={e => { if (e.key === 'Enter') doSave() }}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setSaveModalOpen(false)}>Cancel</button>
              <button className="btn-primary" onClick={doSave}>Save</button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
