import axios from 'axios'

const api = axios.create({
  baseURL: (import.meta as any).env.VITE_API_URL ? `${(import.meta as any).env.VITE_API_URL}/api` : '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ── Typed API helpers ─────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    api.post('/auth/register', { email, password, name }),
  me: () => api.get('/auth/me'),
}

export const automationsApi = {
  list: (ig_account_id?: string) =>
    api.get('/automations/', { params: { ig_account_id } }),
  create: (data: any) => api.post('/automations/', data),
  get: (id: string) => api.get(`/automations/${id}`),
  update: (id: string, data: any) => api.patch(`/automations/${id}`, data),
  delete: (id: string) => api.delete(`/automations/${id}`),
  getFlow: (id: string) => api.get(`/automations/${id}/flow`),
  saveFlow: (id: string, data: any) => api.put(`/automations/${id}/flow`, data),
  publish: (id: string) => api.post(`/automations/${id}/publish`),
  pause: (id: string) => api.post(`/automations/${id}/pause`),
}

export const instagramApi = {
  getAccounts: () => api.get('/instagram/accounts'),
  getCapabilities: (id: string) => api.get(`/instagram/accounts/${id}/capabilities`),
  startOAuth: () => api.get('/instagram/oauth/start'),
  disconnect: (id: string) => api.delete(`/instagram/accounts/${id}`),
}

export const analyticsApi = {
  overview: (params?: any) => api.get('/analytics/overview', { params }),
  automationAnalytics: (id: string, params?: any) =>
    api.get(`/analytics/automations/${id}`, { params }),
}

export const contactsApi = {
  list: (params?: any) => api.get('/contacts/', { params }),
  get: (id: string) => api.get(`/contacts/${id}`),
  timeline: (id: string) => api.get(`/contacts/${id}/timeline`),
}

export const linksApi = {
  list: (params?: any) => api.get('/links/', { params }),
  create: (data: any) => api.post('/links/', data),
  delete: (id: string) => api.delete(`/links/${id}`),
}

export const campaignsApi = {
  list: (params?: any) => api.get('/campaigns/', { params }),
  create: (data: any) => api.post('/campaigns/', data),
  delete: (id: string) => api.delete(`/campaigns/${id}`),
}

export const tagsApi = {
  list: (params?: any) => api.get('/tags/', { params }),
  create: (data: any) => api.post('/tags/', data),
  delete: (id: string) => api.delete(`/tags/${id}`),
}

export const logsApi = {
  list: (params?: any) => api.get('/logs/', { params }),
}

export const inboxApi = {
  conversations: (params?: any) => api.get('/inbox/conversations', { params }),
  messages: (id: string) => api.get(`/inbox/conversations/${id}/messages`),
}
