import { defineStore } from 'pinia'
import api from './api'

export const useAuth = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null as null | { user_id: number; username: string }
  }),
  actions: {
    async login(username: string, password: string) {
      const { data } = await api.post('/auth/login', { username, password })
      this.token = data.data.access_token
      localStorage.setItem('token', this.token)
      await this.me()
    },
    async register(username: string, password: string) {
      await api.post('/auth/register', { username, password })
    },
    async me() {
      if (!this.token) return
      const { data } = await api.get('/auth/me')
      this.user = data.data
    },
    async changePassword(old_password: string, new_password: string) {
      const { data } = await api.post('/auth/change_password', { old_password, new_password })
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
