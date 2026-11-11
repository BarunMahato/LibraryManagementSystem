import axios from 'axios'

const api = axios.create({ baseURL: 'http://127.0.0.1:8000', headers: { 'Content-Type': 'application/json' } })
let refreshing
export const getAccess = () => localStorage.getItem('access_token')
export const saveTokens = ({ access, refresh }) => { if (access) localStorage.setItem('access_token', access); if (refresh) localStorage.setItem('refresh_token', refresh) }
export const clearTokens = () => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token') }
api.interceptors.request.use((config) => { const token = getAccess(); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
api.interceptors.response.use((response) => response, async (error) => {
  const request = error.config
  if (error.response?.status !== 401 || !request || request._retried || /auth\/(login|refresh)/.test(request.url || '')) return Promise.reject(error)
  const refresh = localStorage.getItem('refresh_token')
  try {
    if (!refresh) throw error
    request._retried = true
    refreshing ||= axios.post('http://127.0.0.1:8000/api/auth/refresh/', { refresh })
    const { data } = await refreshing
    refreshing = undefined
    saveTokens({ access: data.access, refresh: data.refresh || refresh })
    request.headers.Authorization = `Bearer ${data.access}`
    return api(request)
  } catch (cause) {
    refreshing = undefined; clearTokens()
    window.dispatchEvent(new CustomEvent('auth:logout', { detail: { message: 'Your session expired. Please sign in again.' } }))
    return Promise.reject(cause)
  }
})
export default api
