import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import NewGameView from './views/NewGameView.vue'
import DashboardView from './views/DashboardView.vue'
import ResultView from './views/ResultView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import { setUnauthorizedHandler } from './api/client'
import { createAuthGuard, createUnauthorizedHandler } from './utils/authRouting'
import { useAuthStore } from './stores/authStore'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: NewGameView },
    { path: '/games/:id', component: DashboardView, props: true, meta: { requiresAuth: true } },
    { path: '/games/:id/result', component: ResultView, props: true, meta: { requiresAuth: true } },
    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', component: RegisterView, meta: { guestOnly: true } },
  ],
})

const pinia = createPinia()
router.beforeEach(createAuthGuard(useAuthStore(pinia)))
setUnauthorizedHandler(createUnauthorizedHandler(router))

const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
