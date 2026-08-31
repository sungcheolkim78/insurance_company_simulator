import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../api/client', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}))

import { getCurrentUser, login, logout, register } from '../api/client'
import { useAuthStore } from './authStore'

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('authStore.initialize', () => {
  it('인증된 사용자면 authenticated 상태로 복원한다', async () => {
    getCurrentUser.mockResolvedValue({ id: 1, email: 'ceo@example.com' })
    const store = useAuthStore()

    await store.initialize()

    expect(store.status).toBe('authenticated')
    expect(store.user).toEqual({ id: 1, email: 'ceo@example.com' })
    expect(getCurrentUser).toHaveBeenCalledTimes(1)
  })

  it('/auth/me 401이면 anonymous 상태로 복원한다', async () => {
    getCurrentUser.mockRejectedValue(new Error('401'))
    const store = useAuthStore()

    await store.initialize()

    expect(store.status).toBe('anonymous')
    expect(store.user).toBeNull()
  })

  it('여러 번 호출해도 /auth/me 를 한 번만 요청한다', async () => {
    getCurrentUser.mockResolvedValue({ id: 1, email: 'ceo@example.com' })
    const store = useAuthStore()

    await Promise.all([store.initialize(), store.initialize()])
    await store.initialize()

    expect(getCurrentUser).toHaveBeenCalledTimes(1)
  })
})

describe('authStore.login / register', () => {
  it('login 성공 시 사용자를 저장하고 authenticated 상태가 된다', async () => {
    login.mockResolvedValue({ id: 7, email: 'ceo@example.com' })
    const store = useAuthStore()

    const user = await store.login('ceo@example.com', 'long-enough-pass')

    expect(user).toEqual({ id: 7, email: 'ceo@example.com' })
    expect(store.status).toBe('authenticated')
    expect(store.user).toEqual({ id: 7, email: 'ceo@example.com' })
  })

  it('register 성공 시 사용자를 저장하고 authenticated 상태가 된다', async () => {
    register.mockResolvedValue({ id: 9, email: 'new@example.com' })
    const store = useAuthStore()

    const user = await store.register('new@example.com', 'long-enough-pass')

    expect(user).toEqual({ id: 9, email: 'new@example.com' })
    expect(store.status).toBe('authenticated')
    expect(store.user).toEqual({ id: 9, email: 'new@example.com' })
  })

  it('login 실패 시 오류를 그대로 전파하고 authenticated 상태로 가지 않는다', async () => {
    login.mockRejectedValue(new Error('401'))
    const store = useAuthStore()

    await expect(store.login('ceo@example.com', 'wrong-password')).rejects.toThrow('401')
    expect(store.status).not.toBe('authenticated')
    expect(store.user).toBeNull()
  })
})

describe('authStore.logout', () => {
  it('로그아웃하면 사용자 상태를 비우고 anonymous 상태가 된다', async () => {
    login.mockResolvedValue({ id: 7, email: 'ceo@example.com' })
    logout.mockResolvedValue({ logged_out: true })
    const store = useAuthStore()
    await store.login('ceo@example.com', 'long-enough-pass')

    await store.logout()

    expect(logout).toHaveBeenCalledTimes(1)
    expect(store.user).toBeNull()
    expect(store.status).toBe('anonymous')
  })
})
