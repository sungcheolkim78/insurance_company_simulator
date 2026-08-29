import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import NewGameView from './views/NewGameView.vue'
import DashboardView from './views/DashboardView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: NewGameView },
    { path: '/games/:id', component: DashboardView, props: true },
  ],
})

createApp(App).use(createPinia()).use(router).mount('#app')
