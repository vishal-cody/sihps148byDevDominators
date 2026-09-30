import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || ''

export const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jocky_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('jocky_token')
      localStorage.removeItem('jocky_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────────────────
export const authAPI = {
  login: (username: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me: () => api.get('/api/auth/me'),
}

// ── Investigations ────────────────────────────────────────────────────
export const investigationsAPI = {
  list: (status?: string) => api.get('/api/investigations', { params: { status } }),
  get: (id: string) => api.get(`/api/investigations/${id}`),
  create: (data: any) => api.post('/api/investigations', data),
  run: (id: string, payload: any) => api.post(`/api/investigations/${id}/run`, payload),
  stats: () => api.get('/api/investigations/stats'),
}

// ── Hosts ──────────────────────────────────────────────────────────────
export const hostsAPI = {
  list: (status?: string) => api.get('/api/hosts', { params: { status } }),
  get: (id: string) => api.get(`/api/hosts/${id}`),
  stats: () => api.get('/api/hosts/stats'),
}

// ── JOCKY Compiler ────────────────────────────────────────────────────
export const jockyAPI = {
  validate: (source_code: string) => api.post('/api/jocky/validate', { source_code }),
  compile: (source_code: string) => api.post('/api/jocky/compile', { source_code }),
  build: (source_code: string, profile = 'forensic_standard', script_id?: string) =>
    api.post('/api/jocky/build', { source_code, profile, script_id }),
  buildVariant: (build_id: string) => api.post(`/api/jocky/build/${build_id}/variant`),
  saveScript: (data: any) => api.post('/api/jocky/scripts', data),
  listScripts: () => api.get('/api/jocky/scripts'),
  listBuilds: () => api.get('/api/jocky/builds'),
}

// ── Evidence ──────────────────────────────────────────────────────────
export const evidenceAPI = {
  processes: (invId: string, hostId?: string) =>
    api.get(`/api/evidence/${invId}/processes`, { params: { host_id: hostId } }),
  network: (invId: string, hostId?: string) =>
    api.get(`/api/evidence/${invId}/network`, { params: { host_id: hostId } }),
  persistence: (invId: string, hostId?: string) =>
    api.get(`/api/evidence/${invId}/persistence`, { params: { host_id: hostId } }),
  timeline: (invId: string, params?: any) =>
    api.get(`/api/timeline/${invId}`, { params }),
  findings: (invId: string, params?: any) =>
    api.get(`/api/findings/${invId}`, { params }),
  graph: (invId: string) => api.get(`/api/graph/${invId}`),
}

// ── Reports ───────────────────────────────────────────────────────────
export const reportsAPI = {
  generate: (invId: string, format: string) =>
    api.post(`/api/reports/${invId}`, { format }),
  list: (invId: string) => api.get(`/api/reports/${invId}`),
  downloadUrl: (reportId: string) => `${BASE}/api/reports/download/${reportId}`,
}
