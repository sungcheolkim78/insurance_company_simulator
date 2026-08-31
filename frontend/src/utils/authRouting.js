import { useAuthStore } from '../stores/authStore'

export function createAuthGuard(authStore) {
  return async (to) => {
    await authStore.initialize()
    if (to.meta?.requiresAuth && authStore.status !== 'authenticated') {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
    if (to.meta?.guestOnly && authStore.status === 'authenticated') {
      return { path: '/' }
    }
    return true
  }
}

export function createUnauthorizedHandler(router) {
  return () => {
    const authStore = useAuthStore()
    authStore.markAnonymous()
    const current = router.currentRoute.value
    if (current.path !== '/login') {
      router.push({ path: '/login', query: { redirect: current.fullPath } })
    }
  }
}
