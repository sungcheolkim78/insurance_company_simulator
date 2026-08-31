import { defineStore } from 'pinia'
import { getCurrentUser, login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    status: 'unknown', // 'unknown' | 'authenticated' | 'anonymous'
    _initPromise: null,
  }),
  actions: {
    async initialize() {
      if (this.status !== 'unknown') return
      if (!this._initPromise) {
        this._initPromise = (async () => {
          try {
            this.user = await getCurrentUser()
            this.status = 'authenticated'
          } catch {
            this.user = null
            this.status = 'anonymous'
          }
        })()
      }
      await this._initPromise
    },
    markAnonymous() {
      this.user = null
      this.status = 'anonymous'
      this._initPromise = null
    },
    async login(email, password) {
      this.user = await apiLogin(email, password)
      this.status = 'authenticated'
      return this.user
    },
    async register(email, password) {
      this.user = await apiRegister(email, password)
      this.status = 'authenticated'
      return this.user
    },
    async logout() {
      try {
        await apiLogout()
      } finally {
        this.markAnonymous()
      }
    },
  },
})
