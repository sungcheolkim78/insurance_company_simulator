import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  withCredentials: true,
})

const CSRF_COOKIE_NAME = 'insurance_csrf'
const AUTH_URLS = ['/auth/me', '/auth/login', '/auth/register', '/auth/logout']

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

apiClient.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    const token = readCookie(CSRF_COOKIE_NAME)
    if (token) {
      config.headers['X-CSRF-Token'] = token
    }
  }
  return config
})

let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    // Auth endpoints handle their own 401s (login/register forms, session
    // restore); forwarding those to the global handler would cause loops.
    if (status === 401 && onUnauthorized && !AUTH_URLS.some((prefix) => url.startsWith(prefix))) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

export async function register(email, password) {
  const response = await apiClient.post('/auth/register', { email, password })
  return response.data
}

export async function login(email, password) {
  const response = await apiClient.post('/auth/login', { email, password })
  return response.data
}

export async function logout() {
  const response = await apiClient.post('/auth/logout')
  return response.data
}

export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me')
  return response.data
}

export async function listGames() {
  const response = await apiClient.get('/games')
  return response.data
}

export async function createGame(initialCapital, rngSeed, gameLengthTurns) {
  const response = await apiClient.post('/games', {
    initial_capital: initialCapital,
    rng_seed: rngSeed ?? null,
    game_length_turns: gameLengthTurns,
  })
  return response.data
}

export async function getGame(gameId) {
  const response = await apiClient.get(`/games/${gameId}`)
  return response.data
}

export async function getHistory(gameId) {
  const response = await apiClient.get(`/games/${gameId}/history`)
  return response.data
}

export async function getConfig(gameId) {
  const response = await apiClient.get(`/games/${gameId}/config`)
  return response.data
}

export async function submitTurn(gameId, decision) {
  const response = await apiClient.post(`/games/${gameId}/turn`, decision)
  return response.data
}

export async function deleteGame(gameId) {
  await apiClient.delete(`/games/${gameId}`)
}
