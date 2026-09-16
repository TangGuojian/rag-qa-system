import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '')

  async function login(username, password) {
    const res = await authApi.login({ username, password })
    token.value = res.data.token
    role.value = res.data.role
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('role', res.data.role)
  }

  function logout() {
    token.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
  }

  function isAdmin() {
    return role.value === 'admin'
  }

  return { token, role, login, logout, isAdmin }
})
