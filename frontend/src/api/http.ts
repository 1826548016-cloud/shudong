import axios from 'axios'

export const http = axios.create({
  baseURL: '/',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('treehole_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let _refreshing = false
let _refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (!originalRequest || originalRequest._retry) {
      return Promise.reject(error)
    }
    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const refreshToken = localStorage.getItem('treehole_refresh')
    if (!refreshToken) {
      return Promise.reject(error)
    }

    if (_refreshing) {
      return new Promise<string>((resolve, reject) => {
        _refreshQueue.push({ resolve, reject })
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return http(originalRequest)
      })
    }

    _refreshing = true
    originalRequest._retry = true

    try {
      const { data } = await axios.post('/api/auth/token/refresh/', {
        refresh: refreshToken,
      })
      const newAccess = data.access
      localStorage.setItem('treehole_token', newAccess)
      if (data.refresh) {
        localStorage.setItem('treehole_refresh', data.refresh)
      }
      _refreshQueue.forEach((q) => q.resolve(newAccess))
      _refreshQueue = []
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      return http(originalRequest)
    } catch (refreshError) {
      _refreshQueue.forEach((q) => q.reject(refreshError))
      _refreshQueue = []
      localStorage.removeItem('treehole_token')
      localStorage.removeItem('treehole_refresh')
      window.dispatchEvent(new Event('treehole-auth-expired'))
      return Promise.reject(refreshError)
    } finally {
      _refreshing = false
    }
  },
)
