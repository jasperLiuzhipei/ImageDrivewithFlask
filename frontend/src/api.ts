import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE || '/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err.response && err.response.status === 401) {
      // 未认证，清空本地令牌
      localStorage.removeItem('token')
      try {
        const p = window.location.pathname
        if (p !== '/login' && p !== '/register') {
          window.location.replace('/login')
        }
      } catch {}
    }
    return Promise.reject(err)
  }
)

// 请求前后更新活动时间，用于会话过期策略
api.interceptors.request.use((cfg) => {
  try { localStorage.setItem('last_active', String(Date.now())) } catch {}
  return cfg
})
api.interceptors.response.use((resp) => {
  try { localStorage.setItem('last_active', String(Date.now())) } catch {}
  return resp
})

export default api
export const API_BASE = BASE_URL
