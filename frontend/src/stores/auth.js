import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAdmin: (s) => s.user?.role === 'admin',
    isAdvanced: (s) => ['admin', 'advanced'].includes(s.user?.role),
    mustChangePassword: (s) => !!s.user?.must_change_password,
    roleLabel: (s) => {
      const map = { admin: '管理员', advanced: '高级账号', normal: '普通账号' }
      return map[s.user?.role] || ''
    },
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    updateUser(user) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
