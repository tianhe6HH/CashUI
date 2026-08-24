import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { showToast } from 'vant'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 防止多个请求同时 401 时重复跳转
let redirectingToLogin = false

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
      if (!redirectingToLogin && window.location.pathname !== '/login') {
        redirectingToLogin = true
        window.location.replace('/login')
      }
      return Promise.reject(err)
    }
    const msg = err.response?.data?.detail || '请求失败'
    showToast(msg)
    return Promise.reject(err)
  },
)

export default request
