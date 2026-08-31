import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../api/client', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}))

import { getCurrentUser, login } from '../api/client'
import { useAuthStore } from '../stores/authStore'
import { createAuthGuard } from './authRouting'

function buildRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>home</div>' } },
      { path: '/login', component: { template: '<div>login</div>' }, meta: { guestOnly: true } },
      { path: '/register', component: { template: '<div>register</div>' }, meta: { guestOnly: true } },
      { path: '/games/:id', component: { template: '<div>game</div>' }, props: true, meta: { requiresAuth: true } },
      {
        path: '/games/:id/result',
        component: { template: '<div>result</div>' },
        props: true,
        meta: { requiresAuth: true },
      },
    ],
  })
  const authStore = useAuthStore()
  router.beforeEach(createAuthGuard(authStore))
  return router
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.history.replaceState({}, '', '/')
})

describe('createAuthGuard', () => {
  it('익명 사용자가 보호 경로에 접근하면 /login 으로 리다이렉트하고 요청 경로를 보존한다', async () => {
    getCurrentUser.mockRejectedValue(new Error('401'))
    const router = buildRouter()

    await router.push('/games/42')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/games/42')
  })

  it('익명 사용자가 보호 결과 경로에 접근해도 /login 으로 리다이렉트한다', async () => {
    getCurrentUser.mockRejectedValue(new Error('401'))
    const router = buildRouter()

    await router.push('/games/42/result')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/games/42/result')
  })

  it('인증된 사용자는 보호 경로에 접근할 수 있다', async () => {
    getCurrentUser.mockResolvedValue({ id: 1, email: 'ceo@example.com' })
    const router = buildRouter()

    await router.push('/games/42')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/games/42')
  })

  it('인증된 사용자가 /login 에 접근하면 홈으로 리다이렉트한다', async () => {
    getCurrentUser.mockResolvedValue({ id: 1, email: 'ceo@example.com' })
    const router = buildRouter()

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('익명 사용자는 /login 에 머무른다', async () => {
    getCurrentUser.mockRejectedValue(new Error('401'))
    const router = buildRouter()

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('로그인 후 보존된 redirect 경로로 이동할 수 있다', async () => {
    getCurrentUser.mockRejectedValueOnce(new Error('401'))
    const router = buildRouter()
    const store = useAuthStore()

    await router.push('/games/42')
    await router.isReady()
    expect(router.currentRoute.value.query.redirect).toBe('/games/42')

    // the login form logs in through the store, then returns to the
    // preserved redirect target
    login.mockResolvedValue({ id: 1, email: 'ceo@example.com' })
    await store.login('ceo@example.com', 'long-enough-pass')
    await router.push(router.currentRoute.value.query.redirect)

    expect(router.currentRoute.value.path).toBe('/games/42')
  })
})
