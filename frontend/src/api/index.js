import axios from 'axios'
import { ElMessage } from 'element-plus'

// 默认使用相对路径：前端构建产物由后端直接托管时同源即可访问，无需额外配置。
// 需要指向独立的后端服务时，设置 VITE_API_BASE_URL 覆盖即可。
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      window.location.href = '/'
    }
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default api

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  init: () => api.post('/auth/init'),
}

export const kbApi = {
  list: (search) => api.get('/knowledge-bases', { params: { search } }),
  create: (data) => api.post('/knowledge-bases', data),
  update: (id, data) => api.put(`/knowledge-bases/${id}`, data),
  delete: (id) => api.delete(`/knowledge-bases/${id}`),
}

export const docApi = {
  upload: (formData) => api.post('/documents/upload', formData),
  list: (params) => api.get('/documents', { params }),
  delete: (id) => api.delete(`/documents/${id}`),
}

export const qaApi = {
  ask: (data) => api.post('/qa/ask', data),
  feedback: (data) => api.post('/qa/feedback', data),
}

export const historyApi = {
  list: (params) => api.get('/history', { params }),
  delete: (id) => api.delete(`/history/${id}`),
}

export const graphApi = {
  data: () => api.get('/graph/data'),
  build: () => api.post('/graph/build'),
}

export const userApi = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
}

export const configApi = {
  get: () => api.get('/config'),
  update: (data) => api.put('/config', data),
}

export const aiApi = {
  providers: () => api.get('/ai/providers'),
  status: () => api.get('/ai/status'),
  test: (data) => api.post('/ai/test', data),
  models: (data) => api.post('/ai/models', data),
}

export const dashboardApi = {
  kbOverview: () => api.get('/dashboard/kb-overview'),
  qaStats: () => api.get('/dashboard/qa-stats'),
  systemStatus: () => api.get('/dashboard/system-status'),
  hotTopics: () => api.get('/dashboard/hot-topics'),
}
