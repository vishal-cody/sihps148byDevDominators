import { useState } from 'react'
import { Layout, PageHeader } from '@/components/layout/Layout'
import { jockyAPI, reportsAPI } from '@/services/api'
import { investigationsAPI } from '@/services/api'
import { FileText, Download, Loader2, CheckCircle2, RefreshCw } from 'lucide-react'
import { useEffect } from 'react'

export default function Reports() {
  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedInv, setSelectedInv] = useState('')
  const [reports, setReports] = useState<any[]>([])
  const [generating, setGenerating] = useState(false)
  const [format, setFormat] = useState('json')

  useEffect(() => {
    investigationsAPI.list().then(r => {
      setInvestigations(r.data)
      if (r.data.length > 0) setSelectedInv(r.data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedInv) return
    reportsAPI.list(selectedInv).then(r => setReports(r.data))
  }, [selectedInv])

  const generate = async () => {
    setGenerating(true)
    try {
      await reportsAPI.generate(selectedInv, format)
      setTimeout(async () => {
        const r = await reportsAPI.list(selectedInv)
        setReports(r.data)
        setGenerating(false)
      }, 2000)
    } catch { setGenerating(false) }
  }

  return (
    <Layout>
      <PageHeader
        title="Forensic Reports"
        subtitle="Generate and export professional investigation reports"
        badge={{ label: 'PDF • JSON • CSV' }}
        actions={
          <button className="btn-secondary" onClick={() => reportsAPI.list(selectedInv).then(r => setReports(r.data))}>
            <RefreshCw size={14} />
          </button>
        }
      />

      <div style={{ padding: '1.5rem 2rem' }} className="fade-in">
        <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Generate Report</h3>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>Investigation</label>
              <select className="input-field" value={selectedInv} onChange={e => setSelectedInv(e.target.value)}>
                {investigations.map(inv => (
                  <option key={inv.id} value={inv.id}>{inv.case_id} — {inv.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>Format</label>
              <select className="input-field" style={{ width: 120 }} value={format} onChange={e => setFormat(e.target.value)}>
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
            <button className="btn-primary" onClick={generate} disabled={generating || !selectedInv}>
              {generating ? <Loader2 size={15} /> : <FileText size={15} />}
              {generating ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </div>

        {/* Report sections preview */}
        <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
          <h4 style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.75rem', color: '#94a3b8' }}>Report Sections</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            {[
              'Executive Summary', 'Investigation Scope', 'Hosts Investigated',
              'Collection Summary', 'Timeline', 'Process Analysis',
              'Network Analysis', 'Persistence Analysis', 'Evidence',
              'Findings', 'Risk Classification', 'Recommendations',
              'Technical Appendix',
            ].map(s => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#64748b' }}>
                <CheckCircle2 size={12} color="#10b981" /> {s}
              </div>
            ))}
          </div>
        </div>

        {/* Generated reports */}
        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600, fontSize: '0.875rem' }}>
            Generated Reports
          </div>
          {reports.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#475569', fontSize: '0.8rem' }}>
              No reports generated yet. Click "Generate Report" above.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Format</th>
                  <th>Status</th>
                  <th>Size</th>
                  <th>Generated</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.id}>
                    <td className="mono" style={{ fontSize: '0.78rem' }}>{r.filename}</td>
                    <td style={{ textTransform: 'uppercase', fontSize: '0.75rem', color: '#3b82f6' }}>{r.format}</td>
                    <td>
                      <span style={{
                        padding: '0.1rem 0.5rem', borderRadius: 4, fontSize: '0.7rem',
                        background: r.status === 'completed' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                        color: r.status === 'completed' ? '#10b981' : '#f59e0b',
                      }}>{r.status}</span>
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.75rem' }}>
                      {r.file_size_bytes ? `${(r.file_size_bytes / 1024).toFixed(1)} KB` : '—'}
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.75rem' }}>
                      {r.generated_at ? new Date(r.generated_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      {r.status === 'completed' && (
                        <a href={reportsAPI.downloadUrl(r.id)} download className="btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem', textDecoration: 'none' }}>
                          <Download size={12} /> Download
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  )
}
